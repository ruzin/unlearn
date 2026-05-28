from travel_common.logging import get_logger

_log = get_logger(__name__)

_QUOTES: dict[str, dict] = {}


def get_quote(quote_id: str) -> dict:
    return _QUOTES.get(quote_id, {"id": quote_id, "status": "expired"})


def store_quote(quote: dict) -> None:
    _QUOTES[quote["id"]] = quote
