from app.services.tiers import recompute_tier
from app.utils.store import accounts
from travel_common.logging import get_logger

_log = get_logger(__name__)


def award_points(user_id: str, amount: int, reason: str) -> dict:
    acc = accounts.get(user_id)
    if acc is None:
        return {}
    acc.points += amount
    acc.tier = recompute_tier(acc.points)
    _log.info("awarded %s points to %s (%s)", amount, user_id, reason)
    return {"user_id": user_id, "points": acc.points, "tier": acc.tier}


def deduct_points(user_id: str, amount: int) -> dict:
    acc = accounts.get(user_id)
    if acc is None or acc.points < amount:
        return {"ok": False}
    acc.points -= amount
    acc.tier = recompute_tier(acc.points)
    return {"user_id": user_id, "points": acc.points}
