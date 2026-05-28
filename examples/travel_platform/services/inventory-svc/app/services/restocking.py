from app.utils.store import get_record, save_record


def restock_inventory(itinerary_id: str, seats: int) -> dict:
    rec = get_record(itinerary_id)
    rec.total += seats
    rec.available += seats
    save_record(rec)
    return {"itinerary_id": itinerary_id, "total": rec.total}
