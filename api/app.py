import os
from json import JSONDecodeError

from flask import Flask, jsonify, request, redirect, abort
from flask_cors import CORS
from flask_httpauth import HTTPTokenAuth
from flask_migrate import Migrate

from api.errors import LoggedError
from api.handlers import handle_slug_reservation, handle_shorten_url_with_custom_slug, shorten_url_collision_check
from api.models import db
from api.repos import config_app_with_db, UrlEntryRepo, SlugReservationRepo

# app initialization
app = Flask(__name__)
CORS(app)

# load os config:
app.config["ReservationDuration"] = int(os.environ["ReservationDurationInSeconds"])

# database configuration
config_app_with_db(app, db)
url_entry_repo = UrlEntryRepo(app, db)
slug_repo = SlugReservationRepo(app, db)
Migrate(app, db)

# security configuration
auth = HTTPTokenAuth(scheme="Bearer")
allowed_tokens = {os.environ["UrlShortenerAllowedKey"]: "no-security"}

# declare all the reusable responses
with app.app_context():
    # app context is needed for jsonify
    RESPONSE_SUCCESS_EMPTY = "", 204
    RESPONSE_BAD_JSON = jsonify("Bad json supplied or ContentType header is not application/json "), 400
    RESPONSE_BAD_ROOT = jsonify("Bad root type supplied"), 400
    RESPONSE_MISSING_ARGS = jsonify("Missing arguments"), 400
    RESPONSE_BAD_ARGUMENT_TYPES_GENERIC = jsonify("Bad argument types"), 400
    RESPONSE_FAIL_BAD_URL = jsonify("URL too long or not a string"), 400
    RESPONSE_FAIL_EMPTY_VALUES_GENERIC = jsonify("Empty/Null values for non-nullable params"), 400
    RESPONSE_FAIL_UNAUTHORIZED_GENERIC = jsonify("No access to the resource"), 403
    RESPONSE_FAIL_METHOD_NOT_ALLOWED = jsonify("Method not allowed"), 405
    RESPONSE_FAIL_UNKNOWN = jsonify("Failed for unknown reasons"), 500

# LOGGER MESSAGES:
ftp = "Failed to process, "
LOG_BAD_JSON = LoggedError(app, ftp + "the request is a bad json")
LOG_BAD_ROOT = LoggedError(app, ftp + "the root is not of required format, {} needed, found: {}")
LOG_MISSING_ARGS = LoggedError(app, ftp + "the request is missing arguments {}")
LOG_BAD_ARGUMENT_TYPES_GENERIC = LoggedError(app, ftp + "the arguments are of the wrong type")
LOG_BAD_ARGUMENT_TYPES = LoggedError(app, ftp + "the arguments are of the wrong type {} should be {} but is {}")
LOG_ALREADY_RESERVED = LoggedError(app, ftp + "the resource has already been reserved by somebody else")
LOG_FAIL_UNKNOWN = LoggedError(app, ftp + "unknown reason, place: {}")

API_PREFIX = 'api'


@auth.verify_token
def verify_token(token: str) -> str:
    return allowed_tokens[token] if token in allowed_tokens else None


@app.route(f"/{API_PREFIX}/shorten", methods=["POST"])
@auth.login_required
def shorten_url():
    response_list = []
    try:
        data = request.json

        # Make sure of the proper data format, to prevent any security issues
        if type(data) is list:
            # Proper data format
            for entry in data:
                # Type of each entry should be dict
                if type(entry) is dict:
                    entry: dict

                    allowed_keys = ["sms_record_id", "original_url"]
                    current_entry_id = None
                    current_entry_url = None

                    # Parse the current entry
                    for key, value in entry.items():
                        if key not in allowed_keys:
                            # Key not understood
                            app.logger.error(f"Failure: Key \"{key}\" not understood")
                            abort(400)
                        else:
                            # assign parameters to their proper value
                            if key == 'original_url':
                                current_entry_url = value
                            elif key == "sms_record_id":
                                current_entry_id = value

                            # If all the parameters have been parsed, shorten and add to the list
                            if current_entry_id is not None and current_entry_url is not None:
                                app.logger.info(f"Request to shorten: {current_entry_url}")
                                shorter_url = shorten_url_collision_check(url_entry_repo, current_entry_id, "",
                                                                          current_entry_url)
                                response_list.append({"sms_record_id": current_entry_id,
                                                      "original_url": current_entry_url,
                                                      "shortened_url": shorter_url})
                else:
                    # The entry is not a dictionary
                    try:
                        string_repr = str(entry)
                        if len(string_repr) > 100:
                            app.logger.error("Failure: The current entry is not a dictionary, "
                                             "but the string representation is very long.")
                        else:
                            app.logger.error(f"Failure: The current entry \"{string_repr}\" is not a dictionary.")
                    except Exception:
                        app.logger.error(
                            f"Failure: The current entry is not a dictionary, and cannot be converted to string.")
                    return jsonify("trying to parse the request, encountered a non-dictionary in the main list"), 400
        else:
            app.logger.error("Failure: The body of the request was not a list")
            return jsonify("while trying to parse the request, the root object is not a dictionary"), 400
        return jsonify(response_list)
    except JSONDecodeError:
        app.logger.error("Failed: The request could not be decoded as JSON.")
        return jsonify("either the request is not json (application/json) header, or failed to parse the body to "
                       "a valid json")


@app.route(f"/{API_PREFIX}/shorten/custom", methods=["POST"])
@auth.login_required
def shorten_url_to_custom():
    """
    Processes the request /shorten/custom/, validating it according to /docs/openapi.json
    :return: the response json
    """
    try:
        req = request.json
        if type(req) is not dict:
            # bad root
            LOG_BAD_ROOT("dict", str(type(req)))
            return RESPONSE_BAD_ROOT

        if "custom_url" not in req:
            LOG_MISSING_ARGS("custom_url")
            return RESPONSE_MISSING_ARGS
        if "custom_url_token" not in req:
            LOG_MISSING_ARGS("custom_url_token")
            return RESPONSE_MISSING_ARGS
        if "urls_to_shorten" not in req:
            LOG_MISSING_ARGS("urls_to_shorten")
            return RESPONSE_MISSING_ARGS

        custom_url = req["custom_url"]
        custom_url_token = req["custom_url_token"]
        urls_to_shorten = req["urls_to_shorten"]

        if type(custom_url) is not str:
            LOG_BAD_ARGUMENT_TYPES("custom_url", "str", str(type(custom_url_token)))
            return RESPONSE_BAD_ARGUMENT_TYPES_GENERIC

        if type(custom_url_token) is not str:
            LOG_BAD_ARGUMENT_TYPES("custom_url_token", "str", str(type(custom_url_token)))
            return RESPONSE_BAD_ARGUMENT_TYPES_GENERIC

        if type(urls_to_shorten) is not list:
            LOG_BAD_ARGUMENT_TYPES("urls_to_shorten", "list", str(type(custom_url_token)))
            return RESPONSE_BAD_ARGUMENT_TYPES_GENERIC

        checked_urls_to_shorten = []
        for ind, i in enumerate(urls_to_shorten):
            if type(i) is not dict:
                LOG_BAD_ARGUMENT_TYPES(f"urls_to_shorten[{ind}]", "dict", type(i))
                return RESPONSE_BAD_ARGUMENT_TYPES_GENERIC
            if "sms_record_id" not in i:
                LOG_MISSING_ARGS(f"urls_to_shorten[{ind}].sms_record_id")
                return RESPONSE_BAD_ARGUMENT_TYPES_GENERIC
            if "original_url" not in i:
                LOG_MISSING_ARGS(f"urls_to_shorten[{ind}].original_url")
                return RESPONSE_BAD_ARGUMENT_TYPES_GENERIC
            sms_record_id = i['sms_record_id']
            original_url = i['original_url']
            if type(sms_record_id) is not str:
                LOG_BAD_ARGUMENT_TYPES(f'urls_to_shorten[{ind}].sms_record_id', 'str', str(type(sms_record_id)))
                return RESPONSE_BAD_ARGUMENT_TYPES_GENERIC

            if type(original_url) is not str:
                LOG_BAD_ARGUMENT_TYPES(f'urls_to_shorten[{ind}].original_url', 'str', str(type(original_url)))
                return RESPONSE_BAD_ARGUMENT_TYPES_GENERIC
            checked_urls_to_shorten.append((original_url, sms_record_id))

        # Validation complete
        result = handle_shorten_url_with_custom_slug(slug_repo, url_entry_repo, custom_url_token, custom_url,
                                                     checked_urls_to_shorten)
        # result[0] = shortened_url_list or None, response_status_code
        if result[0] is None:
            # failed to process
            if result[1] == 400:
                # the company/slug is empty
                LOG_BAD_ARGUMENT_TYPES(f'company_name/slug', 'non-empty', f"{custom_url_token}/{custom_url}")
                return RESPONSE_FAIL_EMPTY_VALUES_GENERIC
            elif result[1] == 403:
                # the slug was already reserved
                LOG_ALREADY_RESERVED()
                return RESPONSE_FAIL_UNAUTHORIZED_GENERIC

            # Unknown error, this branch should not be reachable
            LOG_FAIL_UNKNOWN("shortening custom url list, result is None, not recognized error code")
            return RESPONSE_FAIL_UNKNOWN

        # the processed has finished
        return jsonify(result[0])

    except JSONDecodeError:
        LOG_BAD_JSON()
        return RESPONSE_BAD_JSON


@app.route(f"/{API_PREFIX}/reserve-slug", methods=["POST"])
@auth.login_required
def reserve_slug():
    """
    Handler for the route /reserve-slug/
    :return:
    """

    BAD_PARAMS_MSG = "The company_id/slug do not respect the requirements or are missing"
    # Parse the body, requirements described in docs/openapi.json
    try:
        req = request.json
        if type(req) is dict:
            if "companyId" in req and "slug" in req:
                company_id = req["companyId"]
                slug = req["slug"]
                if type(company_id) is str and type(slug) is str:
                    # Validation complete
                    reservation = handle_slug_reservation(slug_repo, company_id, slug)
                    # reservation[0] - success/failure [1] - reason
                    if reservation[0]:
                        return RESPONSE_SUCCESS_EMPTY
                    elif reservation[1] == 400:
                        # Empty params supplied
                        LOG_BAD_ARGUMENT_TYPES_GENERIC()
                        return jsonify(BAD_PARAMS_MSG), 400
                    else:
                        LoggedError(app, ftp + "slug already taken")()
                        return jsonify("Slug already taken"), 409
                else:
                    # Bad params supplied
                    LOG_BAD_ARGUMENT_TYPES_GENERIC()
                    return jsonify(BAD_PARAMS_MSG), 400
            else:
                # Missing required params
                if "companyId" in req:
                    LOG_MISSING_ARGS("slug")
                else:
                    LOG_MISSING_ARGS("companyId")
                return jsonify(BAD_PARAMS_MSG), 400
        else:
            # Root component is not dict
            LOG_BAD_ROOT("dict", type(req))
            return jsonify("The root component is not a dict"), 400

    except JSONDecodeError:
        # Not a JSON request
        LOG_BAD_JSON()
        return jsonify("Failed to parse the json request"), 400


@app.route("/<company_slug>/<url>", methods=["GET"])
def get_custom_company_url(company_slug: str, url: str):
    """
    Handles the redirect functionality when the user follows a company custom slug
    :param company_slug: the company slug
    :param url: the shortened url
    :return: a json response with code
    """
    # Type checks to prevent malicious urls
    if type(company_slug) is not str or len(url) > 50:
        return "company slug not found in the database", 404
    if company_slug == 'api':
        return RESPONSE_FAIL_METHOD_NOT_ALLOWED
    if type(url) is not str or len(url) > 10:
        return "url not found in the database", 404

    # return the redirect if exists or a 404 if it doesn't
    long_url = url_entry_repo.by_company_slug_and_shorten_url(company_slug, url)

    # url/company not found
    if long_url is None: return jsonify("url/company combination was not found"), 404

    # return the redirect
    return redirect(long_url)


@app.route("/<url>", methods=["GET"])
def get_url(url: str):
    """
    Route handler for /<url>. Redirect a user to the longer url stored in the database
    :param url: the short url to search for
    :return: a redirect (long url, 302) to the final destination
    """
    # Type checks to prevent malicious urls
    if type(url) is not str or len(url) > 10:
        LOG_BAD_ARGUMENT_TYPES("url", "str, len<10", f"{type(url)}, {len(url)}")
        return RESPONSE_FAIL_BAD_URL

    if url == 'shorten':
        # the shorten url is not available with a get method
        abort(405)

    app.logger.info(f"Handling request {url}")
    # try to retrieve the long url
    long_url = url_entry_repo.by_company_slug_and_shorten_url(None, url)

    # check if the url exists
    if long_url is None: return jsonify("url not found"), 404

    # since the url exists, return a redirect
    return redirect(long_url)


if __name__ == '__main__':
    app.run("0.0.0.0", 8000)
