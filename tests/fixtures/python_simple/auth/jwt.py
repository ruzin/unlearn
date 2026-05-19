import hmac
import hashlib
from typing import Optional
from models.user import User

SECRET_KEY = "secret"

def validate_token(token: str) -> Optional[dict]:
    """Validate a JWT token and return the payload."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    payload = decode_payload(parts[1])
    if not verify_signature(token, SECRET_KEY):
        return None
    return payload

def generate_token(user: User) -> str:
    """Generate a JWT token for a user."""
    payload = {"user_id": user.id, "email": user.email}
    return encode_and_sign(payload, SECRET_KEY)

def decode_payload(encoded: str) -> dict:
    """Decode a base64 JWT payload."""
    import json, base64
    return json.loads(base64.b64decode(encoded))

def verify_signature(token: str, secret: str) -> bool:
    """Verify the HMAC signature of a token."""
    parts = token.split(".")
    signing_input = f"{parts[0]}.{parts[1]}"
    expected = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, parts[2])

def encode_and_sign(payload: dict, secret: str) -> str:
    """Encode payload and create signed JWT."""
    import json, base64
    header = base64.b64encode(b'{"alg":"HS256"}').decode()
    body = base64.b64encode(json.dumps(payload).encode()).decode()
    sig = hmac.new(secret.encode(), f"{header}.{body}".encode(), hashlib.sha256).hexdigest()
    return f"{header}.{body}.{sig}"
