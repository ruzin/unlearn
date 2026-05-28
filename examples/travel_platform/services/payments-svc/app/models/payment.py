from dataclasses import dataclass
from decimal import Decimal

from travel_common.currency import Currency


@dataclass
class Charge:
    id: str
    booking_id: str
    amount: Decimal
    currency: Currency
    status: str


@dataclass
class Refund:
    id: str
    charge_id: str
    amount: Decimal
    currency: Currency
