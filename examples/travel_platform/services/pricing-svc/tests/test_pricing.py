from decimal import Decimal

from app.services.pricing import compute_price


def test_compute_price_returns_money():
    money = compute_price("it_abc", Decimal("100"), "USD")
    assert money.amount > Decimal("100")
    assert money.currency.value == "USD"
