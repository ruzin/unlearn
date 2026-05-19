from routes.users import get_user, create_user, list_users
from routes.payments import create_payment_endpoint, get_user_payments

ROUTES = {
    "GET /users": list_users,
    "GET /users/:id": get_user,
    "POST /users": create_user,
    "POST /payments": create_payment_endpoint,
    "GET /payments": get_user_payments,
}

def create_app():
    """Create and configure the application."""
    return ROUTES
