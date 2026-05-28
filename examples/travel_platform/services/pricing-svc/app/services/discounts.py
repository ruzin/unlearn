"""Promo / discount application."""

from decimal import Decimal

from travel_common.currency import Currency, format_currency
from travel_common.logging import get_logger

_log = get_logger(__name__)

_PROMOS = {
    "SUMMER10": Decimal("0.10"),
    "WELCOME5": Decimal("0.05"),
    "LOYALTY15": Decimal("0.15"),
}


def apply_promo(promo_code: str, amount: Decimal, currency: Currency) -> Decimal:
    pct = _PROMOS.get(promo_code.upper())
    if pct is None:
        return amount
    discounted = amount * (Decimal("1") - pct)
    _log.info(
        "promo %s applied: %s -> %s",
        promo_code,
        format_currency(amount, currency),
        format_currency(discounted, currency),
    )
    return discounted
