import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, redirect
from flask_httpauth import HTTPTokenAuth
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from api.short_func import UUID4BasedURLShortener
from db.DBInterface import DB


class PostgresDb(DB):
    db: SQLAlchemy

    def __init__(self, flaskApp: Flask):
        with open(Path(__file__).parent / "secrets.json", "r") as f:
            configData = json.load(f)

        url = f"postgresql://{configData['user']}:{configData['password']}@{configData['host']}:" + \
              f"{configData['port']}/{configData['database']}"
        print(url)
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
        return UrlEntryModel.query.filter_by(id=short_url).first().longUrl

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


@app.route("/shorten")
@auth.login_required
def shorten_url():
    url_to_shorten = request.args.get("u")
    shorter_url = UUID4BasedURLShortener.get_shorter_url_for(url_to_shorten)
    db.create_url_entry(url_to_shorten, shorter_url)
    return jsonify(shorter_url)


@app.route("/<url>")
def get_url(url: str):
    print("request is going ok")
    print(url)
    if type(url) is not str or len(url) > 10:
        return ""
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
