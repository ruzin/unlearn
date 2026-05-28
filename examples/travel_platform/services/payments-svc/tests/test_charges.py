from decimal import Decimal

from app.services.charges import create_charge
from travel_common.currency import Currency


def test_create_charge():
    out = create_charge("bk_test", Decimal("49.99"), Currency.USD)
    assert out["currency"] == "USD"
