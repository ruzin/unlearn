from fastapi import APIRouter

from app.services.package_search import search_packages

router = APIRouter(prefix="/search/packages", tags=["packages"])


@router.get("")
def search(origin: str, destination: str, currency: str = "USD") -> dict:
    return {"results": search_packages(origin, destination, currency)}
