from app.services.flight_search import search_flights


def test_search_flights_returns_results():
    assert len(search_flights("JFK", "LHR")) > 0
