from travel_common.errors import BookingError
from travel_common.logging import get_logger

_log = get_logger(__name__)


def modify_booking(booking_id: str, changes: dict) -> dict:
    if "passenger_ids" in changes and not changes["passenger_ids"]:
        raise BookingError("must have at least one passenger")
    _log.info("modified %s: %s", booking_id, list(changes))
    return {"id": booking_id, "status": "modified"}
