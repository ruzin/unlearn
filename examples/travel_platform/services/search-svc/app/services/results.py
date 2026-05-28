"""Search-result formatting — uses format_currency for display strings."""

from app.models.result import SearchResult
from travel_common.currency import format_currency


def format_results(results: list[SearchResult], currency: str) -> list[dict]:
    return [
        {
            "itinerary_id": r.itinerary_id,
            "title": r.title,
            "amount": str(r.base_amount),
            "currency": currency,
            "display": format_currency(r.base_amount, currency),
        }
        for r in results
    ]
