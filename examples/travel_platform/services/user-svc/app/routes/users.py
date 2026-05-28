from fastapi import APIRouter

from app.services.user_service import create_user, get_user
from app.models.requests import CreateUserRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.post("")
def create(req: CreateUserRequest) -> dict:
    return create_user(req)


@router.get("/{user_id}")
def get(user_id: str) -> dict:
    return get_user(user_id)
