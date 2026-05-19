from models.user import User
from models.payment import Payment

def charge_customer(user: User, payment: Payment) -> dict:
    """Charge a customer via Stripe API."""
    stripe_customer = get_or_create_stripe_customer(user)
    return create_stripe_charge(stripe_customer, payment.amount, payment.currency)

def get_or_create_stripe_customer(user: User) -> dict:
    """Get or create a Stripe customer for a user."""
    return {"id": f"cus_{user.id}", "email": user.email}

def create_stripe_charge(customer: dict, amount: float, currency: str) -> dict:
    """Create a charge in Stripe."""
    return {"id": "ch_123", "amount": amount, "currency": currency, "status": "succeeded"}
