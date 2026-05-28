from decimal import Decimal

from app.models.result import SearchResult


def search_flights(origin: str, destination: str) -> list[SearchResult]:
    return [
        SearchResult(
            itinerary_id=f"it_fl_{origin}_{destination}_{i}",
            title=f"{origin}-{destination} flight {i}",
            base_amount=Decimal("450.00") + Decimal(i * 25),
            currency="USD",
        )
        for i in range(5)
    ]
