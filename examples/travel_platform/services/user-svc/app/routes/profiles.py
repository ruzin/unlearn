from fastapi import APIRouter

from app.services.profile_service import update_profile

router = APIRouter(prefix="/users", tags=["profiles"])


@router.patch("/{user_id}/profile")
def update(user_id: str, changes: dict) -> dict:
    return update_profile(user_id, changes)
