from app.models.result import SearchResult


def rank_by_price(results: list[SearchResult]) -> list[SearchResult]:
    return sorted(results, key=lambda r: r.base_amount)
