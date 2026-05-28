from decimal import Decimal

from app.services.payment_client import charge_for_booking
from app.services.itinerary import release_inventory
from travel_common.currency import Currency, format_currency
from travel_common.errors import BookingError, PaymentError
from travel_common.logging import get_logger

_log = get_logger(__name__)


def handle_confirm(booking_id: str) -> dict:
    try:
        receipt = charge_for_booking(booking_id)
    except PaymentError as e:
        release_inventory(booking_id)
        raise BookingError(
            f"payment failed: {e}", code="booking/payment_failed"
        ) from e

    display = format_currency(Decimal(receipt["amount"]), receipt["currency"])
    _log.info("confirmed %s: %s", booking_id, display)
    return {
        "id": booking_id,
        "status": "confirmed",
        "charged": display,
    }
