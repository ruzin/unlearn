from fastapi import APIRouter

from app.services.locking import acquire_lock, release_lock

router = APIRouter(prefix="/inventory", tags=["locks"])


@router.post("/lock")
def lock(itinerary_id: str, seats: int) -> dict:
    return acquire_lock(itinerary_id, seats)


@router.post("/release")
def release(itinerary_id: str) -> dict:
    return release_lock(itinerary_id)
