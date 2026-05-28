from fastapi import APIRouter

from app.handlers.create import handle_create
from app.handlers.confirm import handle_confirm
from app.models.requests import CreateBookingRequest

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("")
def create(req: CreateBookingRequest) -> dict:
    return handle_create(req)


@router.post("/{booking_id}/confirm")
def confirm(booking_id: str) -> dict:
    return handle_confirm(booking_id)
