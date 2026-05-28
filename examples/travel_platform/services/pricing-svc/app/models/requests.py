from dataclasses import dataclass


@dataclass
class PriceRequest:
    itinerary_id: str
    base_amount: str
    currency: str
    promo_code: str | None = None
