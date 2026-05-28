from travel_common.logging import get_logger

_log = get_logger(__name__)


def handle_event(event: dict) -> dict:
    event_type = event.get("type", "unknown")
    _log.info("webhook received: %s", event_type)
    return {"received": True, "type": event_type}
