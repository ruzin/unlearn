"""Core pricing logic — composes base fare, taxes, surcharges, discounts."""

from decimal import Decimal

from app.services.taxes import compute_tax
from app.services.surcharges import compute_surcharge
from app.utils.rounding import round_money
from travel_common.currency import Currency, format_currency
from travel_common.logging import get_logger
from travel_common.models import Money

_log = get_logger(__name__)


def compute_price(
    itinerary_id: str, base_amount: Decimal, currency: str | Currency
) -> Money:
    code = currency if isinstance(currency, Currency) else Currency(currency)
    tax = compute_tax(base_amount, code)
    surcharge = compute_surcharge(itinerary_id, code)
    total = round_money(base_amount + tax + surcharge, code)
    _log.info("priced %s -> %s", itinerary_id, format_currency(total, code))
    return Money(amount=total, currency=code)
