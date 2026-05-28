from decimal import Decimal

from travel_common.currency import Currency


def call_gateway(action: str, amount: Decimal, currency: Currency) -> dict:
    return {"ok": True, "action": action, "amount": str(amount), "currency": currency.value}
