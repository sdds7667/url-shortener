from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Tuple, Optional, List, Union

from api.repos import SlugReservationRepo

from api.repos import UrlEntryRepo
from api.short_func import UUID4BasedURLShortener


@dataclass
class ShorteningResult:
    sms_record_id: str
    original_url: str
    shortened_url: str


_RESERVED_SLUGS = ["none", "add"]


def handle_slug_reservation(slug_repo: SlugReservationRepo, company_id: str, slug: str) -> Tuple[bool, int]:
    """
    handler for the slug reservation.
    :param slug_repo: the repository interface for the slug reservations
    :param company_id: the id (str) of the company. should be not null, and not empty
    :param slug: the slug that needs to be reserved. should be not null and not empty
    :return: True if the reservation was successful, False otherwise, and the reason (400 - bad params, 409 - duplicate)
    """

    # Check the func prerequisites
    if company_id is None or company_id == "" or slug is None or slug == "":
        return False, 400

    if slug in _RESERVED_SLUGS:
        return False, 409

    # Find the reservation
    existing_reservation = slug_repo.by_id(slug)

    if existing_reservation is None:
        # create the reservation
        slug_repo.add(company_id, slug)
        return True, 204

    elif existing_reservation.by == company_id:
        if not existing_reservation.permanent:
            # the company owns the reservation, refresh it
            slug_repo.refresh(existing_reservation)
        return True, 204
    elif not existing_reservation.permanent and existing_reservation.expires < datetime.now():
        slug_repo.change_reservation(existing_reservation, company_id)
        return True, 204

    # The reservation exists, but is not owned by the company requesting it
    return False, 409


def shorten_url_collision_check(url_repo: UrlEntryRepo, sms_record_id: str, slug: Optional[str], long_url: str) -> str:
    shorter_url = UUID4BasedURLShortener.get_shorter_url_for(long_url)
    while not url_repo.add(sms_record_id, long_url, shorter_url, slug):
        shorter_url = UUID4BasedURLShortener.get_shorter_url_for(long_url)
    return shorter_url


def handle_shorten_url_with_custom_slug(slug_reservation_repo: SlugReservationRepo, url_entry_repo: UrlEntryRepo,
                                        company_token: str, slug: str, urls_to_shorten: List[Tuple[str, str]]
                                        ) -> Tuple[Optional[List[dict]], int]:
    """
    Handles the shortening of the url, adding it to a custom slug; returns the shortened url
    :param slug_reservation_repo: the repository for slug reservations
    :param url_entry_repo: the url entry repo
    :param company_token: the company token (crm_org_id) with which to confirm the validity of the custom token
    :param slug: the slug that will be added to the url
    :param urls_to_shorten: list[original_url, smd_record_id] that will be shortened
    :return: the list of shortened urls, with the long url, the shortened url, and the sms_record_id
    """

    # check the prerequisites
    if company_token == "" or slug == "":
        # neither can be empty
        return None, 400

    reservation = slug_reservation_repo.by_id(slug)
    if reservation is not None:
        if company_token != reservation.by and (reservation.permanent or reservation.expires > datetime.now()):
            # the token is not reserved, and has not expired or is permanent => no access
            return None, 403
        if company_token != reservation.by and reservation.expires < datetime.now():
            slug_reservation_repo.change_reservation(reservation, company_token)

    slug_reservation_repo.reserve_permanently(reservation)

    return_list: List[ShorteningResult] = []

    # the slug is available
    for long_url, sms_record_id in urls_to_shorten:
        shorter_url = slug + "/" + shorten_url_collision_check(url_entry_repo, sms_record_id, slug, long_url)
        return_list.append(ShorteningResult(sms_record_id, long_url, shorter_url))

    return [asdict(x) for x in return_list], 200


def handle_get_slugs_for_company(slug_repo: SlugReservationRepo, companyId: str) -> Union[List[str], int]:
    """
    :param slug_repo: the repository interface for the slug reservations
    :param companyId: the company id that has been used
    :return: the list of slugs the company used
    """
    return slug_repo.by_company_not_expired(companyId)
