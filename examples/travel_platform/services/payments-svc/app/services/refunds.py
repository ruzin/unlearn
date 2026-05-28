from decimal import Decimal

from app.models.payment import Refund
from app.utils.gateway import call_gateway
from travel_common.currency import Currency, format_currency
from travel_common.ids import new_payment_id
from travel_common.logging import get_logger

_log = get_logger(__name__)


def issue_refund(booking_id: str, amount: Decimal, currency: Currency) -> dict:
    gateway = call_gateway("refund", amount, currency)
    refund_id = new_payment_id()
    _log.info(
        "refunded %s for %s",
        format_currency(amount, currency),
        booking_id,
    )
    return {
        "id": refund_id,
        "amount": str(amount),
        "currency": currency.value,
        "ok": gateway["ok"],
    }
