from decimal import Decimal

from fastapi import APIRouter

from app.services.pricing import compute_price
from app.models.requests import PriceRequest
from travel_common.currency import format_currency

router = APIRouter(prefix="/prices", tags=["prices"])


@router.post("/quote")
def quote(req: PriceRequest) -> dict:
    money = compute_price(req.itinerary_id, Decimal(req.base_amount), req.currency)
    return {
        "amount": str(money.amount),
        "currency": money.currency.value,
        "display": format_currency(money.amount, money.currency),
    }
