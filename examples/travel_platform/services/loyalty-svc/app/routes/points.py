from fastapi import APIRouter

from app.services.points import award_points, deduct_points

router = APIRouter(prefix="/loyalty/points", tags=["points"])


@router.post("/award")
def award(user_id: str, amount: int, reason: str = "booking") -> dict:
    return award_points(user_id, amount, reason)


@router.post("/deduct")
def deduct(user_id: str, amount: int) -> dict:
    return deduct_points(user_id, amount)
