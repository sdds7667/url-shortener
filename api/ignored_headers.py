import json
from pathlib import Path
from typing import List

from flask import Flask


def ConfigIgnoredHeaders(flask_app: Flask):
    """
    Loads the ignored-headers.json file into the config values of the application
    """

    ignored_headers_file = Path(flask_app.instance_path).parent / "ignored-headers.json"

    if ignored_headers_file.exists():
        with ignored_headers_file.open("r") as f:
            headers_list: List[str] = json.load(f)
            # to ensure data safety, ignore all the non-string entries
            filter(lambda x: type(x) is str, headers_list)
            flask_app.config["PREVIEW_IGNORED_HEADERS"] = set(headers_list)
    else:
        flask_app.logger.warning("Could not find the ignored-headers.json file. No headers will be ignored")
