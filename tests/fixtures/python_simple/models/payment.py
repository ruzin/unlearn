from dataclasses import dataclass
from models.user import User

@dataclass
class Payment:
    id: int
    user: User
    amount: float
    currency: str = "usd"
    status: str = "pending"

def create_payment(user: User, amount: float) -> Payment:
    """Create a new payment record."""
    return Payment(id=1, user=user, amount=amount)

def get_payments_by_user(user: User) -> list:
    """Get all payments for a user."""
    return []
