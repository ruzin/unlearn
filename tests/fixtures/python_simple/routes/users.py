from auth.middleware import auth_required
from models.user import get_user_by_id, get_user_by_email, User
from services.email import send_welcome_email

@auth_required
def get_user(user_id: int, current_user: dict = None):
    """GET /users/:id"""
    user = get_user_by_id(user_id)
    if user is None:
        return {"error": "Not found"}, 404
    return {"user": user}

@auth_required
def create_user(data: dict, current_user: dict = None):
    """POST /users"""
    user = User(id=0, email=data["email"], name=data["name"])
    send_welcome_email(user)
    return {"user": user}, 201

def list_users():
    """GET /users - no auth required"""
    return {"users": []}
