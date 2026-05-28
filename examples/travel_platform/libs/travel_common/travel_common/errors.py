"""Shared exception hierarchy used across all services."""

from __future__ import annotations


class TravelError(Exception):
    """Base for all travel-platform errors. Carries an error code."""

    code: str = "travel/unknown"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code:
            self.code = code


class BookingError(TravelError):
    code = "booking/failed"


class InventoryError(TravelError):
    code = "inventory/unavailable"


class PaymentError(TravelError):
    code = "payment/failed"


class AuthError(TravelError):
    code = "auth/forbidden"


class ValidationError(TravelError):
    code = "validation/invalid"
