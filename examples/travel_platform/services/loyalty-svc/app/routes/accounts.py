from fastapi import APIRouter

from app.services.accounts import open_account, get_account

router = APIRouter(prefix="/loyalty/accounts", tags=["loyalty-accounts"])


@router.post("")
def open_(user_id: str) -> dict:
    return open_account(user_id)


@router.get("/{user_id}")
def get(user_id: str) -> dict:
    return get_account(user_id)
