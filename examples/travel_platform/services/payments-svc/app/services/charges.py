from decimal import Decimal

from app.models.payment import Charge
from app.utils.gateway import call_gateway
from app.utils.store import store_charge
from travel_common.currency import Currency, format_currency
from travel_common.errors import PaymentError
from travel_common.ids import new_payment_id
from travel_common.logging import get_logger

_log = get_logger(__name__)


def create_charge(booking_id: str, amount: Decimal, currency: Currency) -> dict:
    payment_id = new_payment_id()
    gateway = call_gateway("charge", amount, currency)
    if not gateway["ok"]:
        raise PaymentError("gateway declined")
    charge = Charge(
        id=payment_id,
        booking_id=booking_id,
        amount=amount,
        currency=currency,
        status="captured",
    )
    store_charge(charge)
    _log.info("charged %s for %s", format_currency(amount, currency), booking_id)
    return {
        "id": payment_id,
        "amount": str(amount),
        "currency": currency.value,
    }
