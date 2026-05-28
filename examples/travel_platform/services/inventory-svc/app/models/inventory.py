from dataclasses import dataclass


@dataclass
class InventoryRecord:
    itinerary_id: str
    total: int
    available: int
    locked: int
