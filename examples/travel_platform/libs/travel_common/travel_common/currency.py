"""Currency formatting and conversion utilities.

format_currency() is the canonical formatter used by every service that
displays money to a user. Renaming or changing its signature breaks
pricing, booking, payments, loyalty, and search results.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from travel_common.logging import get_logger

_log = get_logger(__name__)


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    AUD = "AUD"
    CAD = "CAD"
    INR = "INR"


_SYMBOLS = {
    Currency.USD: "$",
    Currency.EUR: "€",
    Currency.GBP: "£",
    Currency.JPY: "¥",
    Currency.AUD: "A$",
    Currency.CAD: "C$",
    Currency.INR: "₹",
}

_DECIMALS = {
    Currency.JPY: 0,
}


@dataclass(frozen=True)
class FormatOptions:
    show_symbol: bool = True
    show_code: bool = False
    grouping: bool = True


def format_currency(
    amount: Decimal | float | int,
    code: str | Currency,
    options: FormatOptions | None = None,
) -> str:
    """Format a monetary amount for display.

    This is THE money formatter for the platform. Every service that
    surfaces a price to a user (search results, booking confirmation,
    payment receipts, loyalty redemption screens) calls this.
    """
    opts = options or FormatOptions()
    currency = code if isinstance(code, Currency) else Currency(code.upper())
    decimals = _DECIMALS.get(currency, 2)

    quantized = Decimal(amount).quantize(Decimal(10) ** -decimals)
    if opts.grouping:
        body = f"{quantized:,.{decimals}f}"
    else:
        body = f"{quantized:.{decimals}f}"

    parts: list[str] = []
    if opts.show_symbol:
        parts.append(_SYMBOLS[currency])
    parts.append(body)
    if opts.show_code:
        parts.append(currency.value)
    return " ".join(parts) if opts.show_code else "".join(parts)


def convert_currency(
    amount: Decimal | float,
    from_code: str | Currency,
    to_code: str | Currency,
    rate: Decimal | float,
) -> Decimal:
    """Convert between currencies using a caller-supplied rate."""
    src = from_code if isinstance(from_code, Currency) else Currency(from_code.upper())
    dst = to_code if isinstance(to_code, Currency) else Currency(to_code.upper())
    if src == dst:
        return Decimal(amount)
    result = Decimal(amount) * Decimal(rate)
    _log.debug("converted %s %s -> %s %s @ %s", amount, src, result, dst, rate)
    return result
