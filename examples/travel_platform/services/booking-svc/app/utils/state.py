"""Booking state machine."""

_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"cancelled", "modified"},
    "modified": {"cancelled"},
    "cancelled": set(),
}


def can_transition(from_state: str, to_state: str) -> bool:
    return to_state in _TRANSITIONS.get(from_state, set())
