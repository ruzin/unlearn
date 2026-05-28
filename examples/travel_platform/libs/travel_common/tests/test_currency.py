from decimal import Decimal

from travel_common.currency import Currency, FormatOptions, format_currency


def test_format_usd_default():
    assert format_currency(Decimal("1234.5"), "USD") == "$1,234.50"


def test_format_jpy_no_decimals():
    assert format_currency(Decimal("1234"), Currency.JPY) == "¥1,234"


def test_format_with_code():
    out = format_currency(Decimal("9.99"), "EUR", FormatOptions(show_code=True))
    assert "EUR" in out
