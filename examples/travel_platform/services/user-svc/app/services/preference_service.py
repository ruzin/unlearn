_PREFS: dict[str, dict] = {}


def set_preferences(user_id: str, prefs: dict) -> dict:
    _PREFS[user_id] = prefs
    return {"id": user_id, "stored": True}


def get_preferences(user_id: str) -> dict:
    return _PREFS.get(user_id, {})
