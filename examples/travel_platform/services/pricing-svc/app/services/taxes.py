from decimal import Decimal

from travel_common.currency import Currency

_RATES = {
    Currency.USD: Decimal("0.08"),
    Currency.EUR: Decimal("0.20"),
    Currency.GBP: Decimal("0.20"),
    Currency.JPY: Decimal("0.10"),
    Currency.AUD: Decimal("0.10"),
    Currency.CAD: Decimal("0.13"),
    Currency.INR: Decimal("0.18"),
}


def compute_tax(amount: Decimal, currency: Currency) -> Decimal:
    return amount * _RATES.get(currency, Decimal("0.10"))
