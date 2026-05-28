from decimal import Decimal

from app.models.result import SearchResult


def search_hotels(city: str) -> list[SearchResult]:
    return [
        SearchResult(
            itinerary_id=f"it_ht_{city}_{i}",
            title=f"Hotel in {city} #{i}",
            base_amount=Decimal("150.00") + Decimal(i * 40),
            currency="USD",
        )
        for i in range(4)
    ]
