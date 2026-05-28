from travel_common.http import ServiceClient
from travel_common.logging import get_logger

_log = get_logger(__name__)
_client = ServiceClient(base_url="http://inventory-svc")


def lock_seats(itinerary_id: str, seats: int) -> bool:
    resp = _client.post(f"/inventory/lock", {"itinerary_id": itinerary_id, "seats": seats})
    return resp.status == 200


def release_seats(itinerary_id: str) -> None:
    _client.post(f"/inventory/release", {"itinerary_id": itinerary_id})
