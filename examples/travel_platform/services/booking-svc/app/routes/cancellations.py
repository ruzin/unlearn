from fastapi import APIRouter

from app.services.cancellation import cancel_booking

router = APIRouter(prefix="/bookings", tags=["cancellations"])


@router.post("/{booking_id}/cancel")
def cancel(booking_id: str, reason: str = "user_request") -> dict:
    return cancel_booking(booking_id, reason)
