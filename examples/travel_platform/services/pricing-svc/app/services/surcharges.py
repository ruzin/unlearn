from decimal import Decimal

from travel_common.currency import Currency


def compute_surcharge(itinerary_id: str, currency: Currency) -> Decimal:
    # Fuel surcharge proxy
    if itinerary_id.startswith("it_long_"):
        return Decimal("45.00")
    return Decimal("12.00")
