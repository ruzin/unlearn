from dataclasses import dataclass
from decimal import Decimal

from travel_common.currency import Currency


@dataclass
class Quote:
    id: str
    itinerary_id: str
    amount: Decimal
    currency: Currency
    breakdown: dict
