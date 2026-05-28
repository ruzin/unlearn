from dataclasses import dataclass
from decimal import Decimal


@dataclass
class SearchResult:
    itinerary_id: str
    title: str
    base_amount: Decimal
    currency: str
