"""Pricing service entry point."""

from fastapi import FastAPI

from app.routes import prices, discounts, quotes
from travel_common.config import load_service_config
from travel_common.logging import get_logger

_log = get_logger(__name__)
config = load_service_config("pricing-svc")

app = FastAPI(title="pricing-svc")
app.include_router(prices.router)
app.include_router(discounts.router)
app.include_router(quotes.router)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": config.name}
