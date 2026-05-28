from app.services.payment_client import refund_for_booking
from app.services.itinerary import release_inventory
from travel_common.logging import get_logger

_log = get_logger(__name__)


def cancel_booking(booking_id: str, reason: str) -> dict:
    refund = refund_for_booking(booking_id)
    release_inventory(booking_id)
    _log.info("cancelled %s (%s)", booking_id, reason)
    return {"id": booking_id, "status": "cancelled", "refund": refund}
