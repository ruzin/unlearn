from auth.middleware import auth_required
from models.user import get_user_by_id
from models.payment import create_payment, get_payments_by_user
from services.stripe import charge_customer

@auth_required
def create_payment_endpoint(data: dict, current_user: dict = None):
    """POST /payments"""
    user = get_user_by_id(current_user["user_id"])
    payment = create_payment(user, data["amount"])
    charge_result = charge_customer(user, payment)
    return {"payment": payment, "charge": charge_result}

@auth_required
def get_user_payments(current_user: dict = None):
    """GET /payments"""
    user = get_user_by_id(current_user["user_id"])
    payments = get_payments_by_user(user)
    return {"payments": payments}
