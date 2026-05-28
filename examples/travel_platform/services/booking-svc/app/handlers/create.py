from decimal import Decimal

from app.models.requests import CreateBookingRequest
from app.services.itinerary import fetch_itinerary, lock_inventory
from app.services.pricing_client import fetch_price
from travel_common.errors import BookingError
from travel_common.ids import new_booking_id
from travel_common.logging import get_logger

_log = get_logger(__name__)


def handle_create(req: CreateBookingRequest) -> dict:
    itinerary = fetch_itinerary(req.itinerary_id)
    if itinerary is None:
        raise BookingError("itinerary not found", code="booking/itinerary_missing")
    lock_inventory(req.itinerary_id, len(req.passenger_ids))
    price = fetch_price(req.itinerary_id, Decimal("0"), "USD", req.promo_code)
    booking_id = new_booking_id()
    _log.info("created booking %s for user %s", booking_id, req.user_id)
    return {
        "id": booking_id,
        "status": "pending",
        "price": price,
    }
