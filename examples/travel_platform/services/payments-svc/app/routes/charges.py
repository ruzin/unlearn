from decimal import Decimal

from fastapi import APIRouter

from app.services.charges import create_charge
from travel_common.currency import format_currency, Currency

router = APIRouter(prefix="/charges", tags=["charges"])


@router.post("")
def create(booking_id: str, amount: str = "499.00", currency: str = "USD") -> dict:
    receipt = create_charge(booking_id, Decimal(amount), Currency(currency))
    return {
        "id": receipt["id"],
        "amount": receipt["amount"],
        "currency": receipt["currency"],
        "display": format_currency(Decimal(receipt["amount"]), receipt["currency"]),
    }
