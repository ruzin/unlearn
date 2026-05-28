from fastapi import APIRouter

from app.services.modification import modify_booking

router = APIRouter(prefix="/bookings", tags=["modifications"])


@router.patch("/{booking_id}")
def modify(booking_id: str, changes: dict) -> dict:
    return modify_booking(booking_id, changes)
