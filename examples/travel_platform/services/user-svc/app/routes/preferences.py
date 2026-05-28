from fastapi import APIRouter

from app.services.preference_service import set_preferences, get_preferences

router = APIRouter(prefix="/users", tags=["preferences"])


@router.put("/{user_id}/preferences")
def set_(user_id: str, prefs: dict) -> dict:
    return set_preferences(user_id, prefs)


@router.get("/{user_id}/preferences")
def get(user_id: str) -> dict:
    return get_preferences(user_id)
