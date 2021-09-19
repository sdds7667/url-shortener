import json
import os
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, redirect, abort
from flask_httpauth import HTTPTokenAuth
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from api.short_func import UUID4BasedURLShortener
from db.DBInterface import DB


class PostgresDb(DB):
    db: SQLAlchemy

    def __init__(self, flaskApp: Flask):
        url = os.environ["DATABASE_URL"]
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        flaskApp.config["SQLALCHEMY_DATABASE_URI"] = url
        flaskApp.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.db = SQLAlchemy(flaskApp)
        self.app = flaskApp

    def create_url_entry(self, long_url: str, short_url: str) -> bool:
        if UrlEntryModel.query.filter_by(id=short_url).first():
            return False
        new_instance = UrlEntryModel(short_url, long_url, 0, datetime.now())
        self.db.session.add(new_instance)
        self.db.session.commit()
        return True

    def get_url_entry(self, short_url: str) -> Optional[str]:
        urlEntryModel: UrlEntryModel = UrlEntryModel.query.filter_by(id=short_url).first()
        if urlEntryModel is None:
            abort(404)
        urlEntryModel.lastUsed = datetime.now()
        urlEntryModel.used = UrlEntryModel.used + 1
        self.db.session.commit()
        return urlEntryModel.longUrl

    def migrate(self):
        migrate = Migrate(self.app, self.db)


app = Flask(__name__)
auth = HTTPTokenAuth(scheme="Bearer")
db = PostgresDb(app)
db.migrate()
allowed_tokens = {os.environ["UrlShortenerAllowedKey"]: "no-security"}


@auth.verify_token
def verify_token(token: str) -> str:
    return allowed_tokens[token] if token in allowed_tokens else None


def shorten_url_collision_check(long_url: str) -> str:
    shorter_url = UUID4BasedURLShortener.get_shorter_url_for(long_url)
    while not db.create_url_entry(long_url, shorter_url):
        shorter_url = UUID4BasedURLShortener.get_shorter_url_for(long_url)
    return shorter_url


@app.route("/shorten", methods=["POST"])
@auth.login_required
def shorten_url():
    url_to_shorten = request.args.get("u")
    if url_to_shorten.startswith("["):
        response_list = []
        try:
            data = json.loads(url_to_shorten)

            # Make sure of the proper data format, to prevent any security issues
            if type(data) is list:
                # Proper data format

                for entry in data:
                    # Type of each entry should be dict
                    if type(entry) is dict:
                        entry: dict

                        allowed_keys = ["sms_record_id", "original_url"]
                        currentEntryId = None
                        currentEntryUrl = None

                        # Parse the current entry
                        for key, value in entry.items():
                            if key not in allowed_keys:
                                # Key not understood
                                abort(400)
                            else:
                                # assign parameters to their proper value
                                if key == 'original_url':
                                    currentEntryUrl = value
                                elif key == "sms_record_id":
                                    currentEntryId = value

                                # If all the parameters have been parsed, shorten and add to the list
                                if currentEntryId is not None and currentEntryUrl is not None:
                                    shorter_url = shorten_url_collision_check(currentEntryUrl)
                                    response_list.append({"sms_record_id": currentEntryId,
                                                          "original_url": currentEntryUrl,
                                                          "shortened_url": shorter_url})
                    else:
                        abort(400)
            else:
                abort(400)
            return jsonify(response_list)
        except JSONDecodeError:
            abort(400)
    else:
        shorter_url = shorten_url_collision_check(url_to_shorten)
        return jsonify(shorter_url)


@app.route("/<url>")
def get_url(url: str):
    if type(url) is not str or len(url) > 10:
        return ""
    if url == 'shorten':
        abort(405)
    return redirect(db.get_url_entry(url))


class UrlEntryModel(db.db.Model):
    id = db.db.Column(db.db.String, primary_key=True)  # Same as the url
    longUrl = db.db.Column(db.db.String)
    used = db.db.Column(db.db.BIGINT)
    lastUsed = db.db.Column(db.db.TIMESTAMP)

    def __init__(self, oId: str, url: str, used: int, lastUsed: datetime):
        self.id = oId
        self.longUrl = url
        self.used = used
        self.lastUsed = lastUsed

    def __repr__(self):
        return f"<{self.id}/{self.longUrl}/{self.used}/{self.lastUsed}>"


if __name__ == '__main__':
    app.run("0.0.0.0", 5000)
