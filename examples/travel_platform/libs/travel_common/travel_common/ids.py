"""ID generation helpers."""

from __future__ import annotations

import secrets
import time


def new_booking_id() -> str:
    return f"bk_{int(time.time())}_{secrets.token_hex(4)}"


def new_payment_id() -> str:
    return f"py_{int(time.time())}_{secrets.token_hex(4)}"


def new_user_id() -> str:
    return f"usr_{secrets.token_hex(8)}"


def new_itinerary_id() -> str:
    return f"it_{secrets.token_hex(6)}"
