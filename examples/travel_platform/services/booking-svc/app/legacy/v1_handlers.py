"""DEAD CODE — old v1 booking handler. Replaced by app/handlers/create.py."""

from decimal import Decimal


def legacy_create_booking(user_id: str, itinerary_id: str, amount: Decimal) -> dict:
    return {
        "id": f"legacy_{user_id}_{itinerary_id}",
        "amount": str(amount),
        "status": "pending",
    }


def legacy_confirm_booking(booking_id: str) -> dict:
    return {"id": booking_id, "status": "confirmed"}


def legacy_cancel_booking(booking_id: str) -> dict:
    return {"id": booking_id, "status": "cancelled"}
