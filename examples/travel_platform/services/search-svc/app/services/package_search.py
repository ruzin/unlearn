from app.services.flight_search import search_flights
from app.services.hotel_search import search_hotels
from app.services.results import format_results


def search_packages(origin: str, destination: str, currency: str) -> list[dict]:
    flights = format_results(search_flights(origin, destination), currency)
    hotels = format_results(search_hotels(destination), currency)
    return [{"flight": f, "hotel": h} for f, h in zip(flights, hotels)]
