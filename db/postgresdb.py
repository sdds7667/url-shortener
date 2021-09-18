import json
from pathlib import Path
from typing import Optional

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from db.DBInterface import DB

if __name__ == '__main__':
    PostgresDb(Flask(__name__)).create_url_entry('a', 'b')
