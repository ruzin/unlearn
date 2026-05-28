from fastapi import APIRouter

from app.services.hotel_search import search_hotels
from app.services.results import format_results

router = APIRouter(prefix="/search/hotels", tags=["hotels"])


@router.get("")
def search(city: str, currency: str = "USD") -> dict:
    raw = search_hotels(city)
    return {"results": format_results(raw, currency)}
