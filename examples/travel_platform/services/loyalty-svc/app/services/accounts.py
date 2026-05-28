from app.models.account import LoyaltyAccount
from app.utils.store import accounts


def open_account(user_id: str) -> dict:
    accounts[user_id] = LoyaltyAccount(user_id=user_id, points=0, tier="bronze")
    return {"user_id": user_id, "tier": "bronze"}


def get_account(user_id: str) -> dict:
    acc = accounts.get(user_id)
    if acc is None:
        return {}
    return {"user_id": acc.user_id, "points": acc.points, "tier": acc.tier}
