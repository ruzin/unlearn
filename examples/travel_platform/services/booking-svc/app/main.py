"""Booking service entry point."""

from fastapi import FastAPI

from app.routes import bookings, cancellations, modifications
from travel_common.config import load_service_config
from travel_common.logging import get_logger

_log = get_logger(__name__)
config = load_service_config("booking-svc")

app = FastAPI(title="booking-svc")
app.include_router(bookings.router)
app.include_router(cancellations.router)
app.include_router(modifications.router)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": config.name}
