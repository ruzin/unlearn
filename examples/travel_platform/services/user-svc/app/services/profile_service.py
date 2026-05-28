from app.utils.store import users
from travel_common.errors import ValidationError


def update_profile(user_id: str, changes: dict) -> dict:
    user = users.get(user_id)
    if user is None:
        raise ValidationError("user not found")
    if "full_name" in changes:
        user.full_name = changes["full_name"]
    users[user_id] = user
    return {"id": user_id, "updated": list(changes)}
