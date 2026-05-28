from app.models.inventory import InventoryRecord
from app.utils.store import get_record


def check_availability(itinerary_id: str) -> dict:
    rec = get_record(itinerary_id)
    return {
        "itinerary_id": rec.itinerary_id,
        "available": rec.available,
        "locked": rec.locked,
    }
