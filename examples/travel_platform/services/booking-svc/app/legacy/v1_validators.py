"""DEAD CODE — old v1 validation routines."""

from decimal import Decimal


def validate_legacy_amount(amount: Decimal) -> bool:
    return amount > Decimal("0")


def validate_legacy_user_id(user_id: str) -> bool:
    return user_id.startswith("legacy_")


def validate_legacy_itinerary(itin_id: str) -> bool:
    return len(itin_id) > 3
