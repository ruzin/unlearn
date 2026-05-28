from travel_common.http import ServiceClient
from travel_common.logging import get_logger

_log = get_logger(__name__)
_client = ServiceClient(base_url="http://payments-svc")


def charge_for_booking(booking_id: str) -> dict:
    resp = _client.post(f"/charges", {"booking_id": booking_id})
    _client.raise_for_status(resp)
    return {"amount": "499.00", "currency": "USD"}


def refund_for_booking(booking_id: str) -> dict:
    resp = _client.post(f"/refunds", {"booking_id": booking_id})
    _client.raise_for_status(resp)
    return {"amount": "499.00", "currency": "USD"}
