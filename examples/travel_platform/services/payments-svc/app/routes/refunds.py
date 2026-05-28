from decimal import Decimal

from fastapi import APIRouter

from app.services.refunds import issue_refund
from travel_common.currency import format_currency, Currency

router = APIRouter(prefix="/refunds", tags=["refunds"])


@router.post("")
def create(booking_id: str, amount: str = "499.00", currency: str = "USD") -> dict:
    receipt = issue_refund(booking_id, Decimal(amount), Currency(currency))
    return {
        "id": receipt["id"],
        "display": format_currency(Decimal(receipt["amount"]), receipt["currency"]),
    }
