from decimal import Decimal

from fastapi import APIRouter

from app.services.redemption import redeem
from travel_common.currency import format_currency, Currency

router = APIRouter(prefix="/loyalty/redemption", tags=["redemption"])


@router.post("/{user_id}")
def redeem_(user_id: str, points: int, currency: str = "USD") -> dict:
    value = redeem(user_id, points)
    return {
        "user_id": user_id,
        "redeemed_points": points,
        "value": format_currency(value, Currency(currency)),
    }
