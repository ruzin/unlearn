from app.models.requests import CreateBookingRequest
from app.handlers.create import handle_create


def test_handle_create_returns_pending():
    req = CreateBookingRequest(
        user_id="usr_1", itinerary_id="it_abc", passenger_ids=["p1"]
    )
    result = handle_create(req)
    assert result["status"] == "pending"
