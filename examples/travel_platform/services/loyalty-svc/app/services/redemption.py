from decimal import Decimal

from app.services.points import deduct_points
from travel_common.currency import format_currency, Currency
from travel_common.logging import get_logger

_log = get_logger(__name__)

_POINT_VALUE = Decimal("0.01")  # 1 point = 1 cent


def redeem(user_id: str, points: int) -> Decimal:
    result = deduct_points(user_id, points)
    if not result.get("ok", True) is False:
        value = Decimal(points) * _POINT_VALUE
        _log.info(
            "redeemed %s pts -> %s", points, format_currency(value, Currency.USD)
        )
        return value
    return Decimal("0")
