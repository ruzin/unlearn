from app.utils.store import get_record, save_record
from travel_common.errors import InventoryError
from travel_common.logging import get_logger

_log = get_logger(__name__)


def acquire_lock(itinerary_id: str, seats: int) -> dict:
    rec = get_record(itinerary_id)
    if rec.available < seats:
        raise InventoryError(f"only {rec.available} seats available")
    rec.available -= seats
    rec.locked += seats
    save_record(rec)
    _log.info("locked %s seats on %s", seats, itinerary_id)
    return {"itinerary_id": itinerary_id, "locked": seats}


def release_lock(itinerary_id: str) -> dict:
    rec = get_record(itinerary_id)
    rec.available += rec.locked
    rec.locked = 0
    save_record(rec)
    _log.info("released locks on %s", itinerary_id)
    return {"itinerary_id": itinerary_id, "released": True}
