from fastapi import APIRouter

from app.services.availability import check_availability

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/{itinerary_id}")
def get(itinerary_id: str) -> dict:
    return check_availability(itinerary_id)
