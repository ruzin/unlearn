from auth.jwt import validate_token, generate_token
from models.user import User

def test_generate_token():
    user = User(id=1, email="test@test.com", name="Test")
    token = generate_token(user)
    assert isinstance(token, str)
    assert len(token.split(".")) == 3

def test_validate_token_invalid():
    result = validate_token("invalid")
    assert result is None
