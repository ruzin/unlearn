from fastapi import APIRouter

from app.services.quotes import get_quote

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("/{quote_id}")
def get(quote_id: str) -> dict:
    return get_quote(quote_id)
