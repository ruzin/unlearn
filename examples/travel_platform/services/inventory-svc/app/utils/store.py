from app.models.inventory import InventoryRecord

_STORE: dict[str, InventoryRecord] = {}


def get_record(itinerary_id: str) -> InventoryRecord:
    if itinerary_id not in _STORE:
        _STORE[itinerary_id] = InventoryRecord(
            itinerary_id=itinerary_id, total=100, available=100, locked=0
        )
    return _STORE[itinerary_id]


def save_record(rec: InventoryRecord) -> None:
    _STORE[rec.itinerary_id] = rec
