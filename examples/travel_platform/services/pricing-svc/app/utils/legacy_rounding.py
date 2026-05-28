"""DEAD CODE — old half-down rounding policy from v0 pricing engine.

Superseded by app/utils/rounding.py. Nothing imports this module.
Kept as a planted dead-code scenario for find_dead_code.
"""

from decimal import ROUND_HALF_DOWN, Decimal


def round_half_down(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)


def round_to_nearest_5(amount: Decimal) -> Decimal:
    return (amount * Decimal("0.2")).quantize(Decimal("1")) * Decimal("5")


def round_to_nearest_10(amount: Decimal) -> Decimal:
    return (amount * Decimal("0.1")).quantize(Decimal("1")) * Decimal("10")
