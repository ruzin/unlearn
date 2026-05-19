from functools import wraps
from auth.jwt import validate_token

def auth_required(f):
    """Decorator that requires a valid auth token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        payload = validate_token(token)
        if payload is None:
            return {"error": "Unauthorized"}, 401
        kwargs["current_user"] = payload
        return f(*args, **kwargs)
    return decorated

def get_token_from_request() -> str:
    """Extract bearer token from request headers."""
    return ""
