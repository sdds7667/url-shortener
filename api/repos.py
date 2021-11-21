import os
from datetime import datetime
from typing import Optional, List

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from api.models import UrlEntryModel, SlugReservation


def config_app_with_db(flask_app: Flask, db: SQLAlchemy):
    url = os.environ["DATABASE_URL"]
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = url
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(flask_app)


class Repo:
    db: SQLAlchemy
    app: Flask

    def __init__(self, app: Flask, db: SQLAlchemy):
        self.db = db
        self.app = app


class UrlEntryRepo(Repo):

    def add(self, record_id: str, long_url: str, short_url: str, company_slug: Optional[str] = "") -> bool:

        # ensure that the company name is never NULL,
        if UrlEntryModel.query.filter_by(id=short_url).first():
            return False
        new_instance = UrlEntryModel(company_slug, short_url, record_id, long_url, 0, datetime.now())

        self.db.session.add(new_instance)
        self.db.session.commit()

        return True

    def by_company_slug_and_shorten_url(self, company_slug: Optional[str], short_url: str) -> Optional[str]:
        """
        Retrieves the longer url from the database
        :param company_slug: the company slug to search for
        :param short_url: the shorter url to search for
        :return: None if the entry was not found, the long url otherwise
        """
        # Ensure that the company slug is never empty
        company_slug = "" if company_slug is None else company_slug

        # Search for the longer url
        urlEntryModel: UrlEntryModel = UrlEntryModel.query.filter_by(companySlug=company_slug, id=short_url).first()

        # if the longer url was not found, stop
        if urlEntryModel is None:
            return None

        # Update the usage stats
        urlEntryModel.lastUsed = datetime.now()
        urlEntryModel.used = UrlEntryModel.used + 1
        self.db.session.commit()

        return urlEntryModel.longUrl


class SlugReservationRepo(Repo):

    @staticmethod
    def by_id(_id: str) -> Optional[SlugReservation]:
        return SlugReservation.query.filter_by(slug=_id).first()

    @staticmethod
    def by_company(companyId: str) -> List[str]:
        slug_reservations: List[SlugReservation] = SlugReservation.query.filter_by(by=companyId).all()
        return list({x.slug for x in slug_reservations})

    def add(self, company_id: str, slug: str) -> SlugReservation:
        """
        Creates a new slug reservation and adds it to the database
        :param company_id: the company id that will be linked to the slug
        :param slug: the slug that is being reserved
        :return: the created instance from the database
        """
        new_reservation = SlugReservation(slug, company_id, False, app=self.app)
        self.db.session.add(new_reservation)
        self.db.session.commit()
        return new_reservation

    def refresh(self, slug_reservation: SlugReservation):
        """
        Refreshes a reservation and commits it to the database
        :param slug_reservation: the linked slug reservation instance
        """
        slug_reservation.refresh(self.app)
        self.db.session.commit()

    def reserve_permanently(self, slug_reservation: SlugReservation):
        slug_reservation.permanent = True
        slug_reservation.expires = None
        self.db.session.commit()

    def change_reservation(self, slug_reservation: SlugReservation, by: str):
        slug_reservation.by = by
        slug_reservation.refresh(self.app)
        self.db.session.commit()
