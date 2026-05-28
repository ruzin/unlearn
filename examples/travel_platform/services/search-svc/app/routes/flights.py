from fastapi import APIRouter

from app.services.flight_search import search_flights
from app.services.results import format_results

router = APIRouter(prefix="/search/flights", tags=["flights"])


@router.get("")
def search(origin: str, destination: str, currency: str = "USD") -> dict:
    raw = search_flights(origin, destination)
    return {"results": format_results(raw, currency)}
