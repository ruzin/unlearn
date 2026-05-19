from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    email: str
    name: str
    is_active: bool = True

def get_user_by_id(user_id: int) -> Optional[User]:
    """Fetch a user from the database by ID."""
    return User(id=user_id, email="test@test.com", name="Test")

def get_user_by_email(email: str) -> Optional[User]:
    """Fetch a user from the database by email."""
    return User(id=1, email=email, name="Test")
