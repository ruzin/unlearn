"""Itinerary fetch + inventory locking. Also surfaces a price display."""

from decimal import Decimal

from app.services.inventory_client import lock_seats, release_seats
from travel_common.currency import format_currency
from travel_common.errors import InventoryError
from travel_common.logging import get_logger

_log = get_logger(__name__)


def fetch_itinerary(itinerary_id: str) -> dict | None:
    return {"id": itinerary_id, "origin": "JFK", "destination": "LHR"}


def lock_inventory(itinerary_id: str, seats: int) -> None:
    locked = lock_seats(itinerary_id, seats)
    if not locked:
        raise InventoryError(f"no inventory for {itinerary_id}")
    _log.info("locked %s seats on %s", seats, itinerary_id)


def release_inventory(itinerary_id: str) -> None:
    release_seats(itinerary_id)


def describe_price(amount: Decimal, currency: str) -> str:
    return format_currency(amount, currency)
