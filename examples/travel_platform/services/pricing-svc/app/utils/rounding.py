"""Money rounding — the active implementation. legacy_rounding.py is unused."""

from decimal import ROUND_HALF_UP, Decimal

from travel_common.currency import Currency

_QUANTUM = {
    Currency.JPY: Decimal("1"),
}


def round_money(amount: Decimal, currency: Currency) -> Decimal:
    q = _QUANTUM.get(currency, Decimal("0.01"))
    return amount.quantize(q, rounding=ROUND_HALF_UP)
