from dataclasses import dataclass


@dataclass
class CreateBookingRequest:
    user_id: str
    itinerary_id: str
    passenger_ids: list[str]
    promo_code: str | None = None
