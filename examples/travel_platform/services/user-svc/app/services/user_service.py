from app.models.requests import CreateUserRequest
from app.utils.store import users
from travel_common.currency import Currency
from travel_common.errors import ValidationError
from travel_common.ids import new_user_id
from travel_common.logging import get_logger
from travel_common.models import User

_log = get_logger(__name__)


def create_user(req: CreateUserRequest) -> dict:
    if "@" not in req.email:
        raise ValidationError("invalid email")
    user = User(
        id=new_user_id(),
        email=req.email,
        full_name=req.full_name,
        home_currency=Currency(req.home_currency),
    )
    users[user.id] = user
    _log.info("created user %s", user.id)
    return {"id": user.id, "email": user.email}


def get_user(user_id: str) -> dict:
    user = users.get(user_id)
    if user is None:
        return {}
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "home_currency": user.home_currency.value,
        "loyalty_tier": user.loyalty_tier,
    }
