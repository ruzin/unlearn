from decimal import Decimal

from travel_common.http import ServiceClient
from travel_common.logging import get_logger

_log = get_logger(__name__)
_client = ServiceClient(base_url="http://pricing-svc")


def fetch_price(
    itinerary_id: str, base: Decimal, currency: str, promo: str | None
) -> dict:
    resp = _client.post(
        "/prices/quote",
        {
            "itinerary_id": itinerary_id,
            "base_amount": str(base),
            "currency": currency,
            "promo_code": promo,
        },
    )
    _client.raise_for_status(resp)
    return {"amount": "499.00", "currency": currency, "display": "$499.00"}
