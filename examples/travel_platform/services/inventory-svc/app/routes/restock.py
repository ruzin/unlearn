from fastapi import APIRouter

from app.services.restocking import restock_inventory

router = APIRouter(prefix="/inventory", tags=["restock"])


@router.post("/restock")
def restock(itinerary_id: str, seats: int) -> dict:
    return restock_inventory(itinerary_id, seats)
