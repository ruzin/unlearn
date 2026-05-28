from decimal import Decimal

from fastapi import APIRouter

from app.services.discounts import apply_promo
from travel_common.currency import format_currency, Currency

router = APIRouter(prefix="/discounts", tags=["discounts"])


@router.post("/apply")
def apply(promo_code: str, amount: str, currency: str) -> dict:
    discounted = apply_promo(promo_code, Decimal(amount), Currency(currency))
    return {
        "amount": str(discounted),
        "display": format_currency(discounted, currency),
    }
