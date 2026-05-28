from app.models.requests import CreateUserRequest
from app.services.user_service import create_user, get_user


def test_create_then_get():
    res = create_user(CreateUserRequest(email="a@b.com", full_name="A B"))
    assert get_user(res["id"])["email"] == "a@b.com"
