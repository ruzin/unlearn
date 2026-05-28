from app.models.payment import Charge

_CHARGES: dict[str, Charge] = {}


def store_charge(charge: Charge) -> None:
    _CHARGES[charge.id] = charge


def get_charge(charge_id: str) -> Charge | None:
    return _CHARGES.get(charge_id)
