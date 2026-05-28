from fastapi import APIRouter

from app.services.webhook_handler import handle_event

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
def stripe(event: dict) -> dict:
    return handle_event(event)
