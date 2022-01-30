from datetime import datetime, timedelta
from typing import Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class UrlEntryModel(db.Model):
    companySlug = db.Column(db.String, primary_key=True)
    id = db.Column(db.String, primary_key=True)  # Same as the url
    recordId = db.Column(db.String)
    longUrl = db.Column(db.String)
    used = db.Column(db.BIGINT)
    lastUsed = db.Column(db.TIMESTAMP)
    synced = db.Column(db.Boolean)

    def __init__(self, companySlug: str, oId: str, recordId: str, url: str, used: int, lastUsed: datetime):
        self.companySlug = companySlug if companySlug is not None else ""
        self.id = oId
        self.recordId = recordId
        self.longUrl = url
        self.used = used
        self.lastUsed = lastUsed
        self.synced = False

    def __repr__(self):
        return f"<{self.companySlug}/{self.id}/{self.longUrl}/{self.used}/{self.lastUsed}>"


class SlugReservation(db.Model):
    """
    Slug Reservation:
    id: the slug itself
    by: the company id that is reserving the slug
    permanent:
        the flow requires the ability to reserve a slug while it confirms all the details
        of the message. the confirmation indicator will appear near the message. if the
        company creates an url with the slug, the reservation becomes permanent, if not,
        the reservation is only temporary, and should expire @expires
    created: the time when the reservation was created.
    expires: if the reservation is permanent, it will never expire (null), else the deadline
        after which the company loses the reservation
    """
    slug = db.Column(db.String, primary_key=True)
    by = db.Column(db.String, nullable=False)
    permanent = db.Column(db.Boolean)
    created = db.Column(db.TIMESTAMP)
    expires = db.Column(db.TIMESTAMP, nullable=True)
    synced = db.Column(db.Boolean)

    def __init__(self, slug: str, by: str, permanent: bool,
                 created: Optional[datetime] = None,
                 expires: Optional[datetime] = None,
                 app: Optional[Flask] = None):
        self.slug = slug
        self.by = by
        self.permanent = permanent
        self.created = created if created is not None else datetime.now()
        reservation_duration = app.config["ReservationDuration"] if app is not None else 900
        self.expires = (self.created + timedelta(seconds=reservation_duration)) if expires is None else expires

    def __repr__(self):
        return f"<SlugReservation \"{self.slug}\" by \"{self.by}\">"

    def refresh(self, app: Optional[Flask] = None):
        reservation_duration = app.config["ReservationDuration"] if app is not None else 900
        self.expires = datetime.now() + timedelta(seconds=reservation_duration)
