from fastapi import FastAPI

from app.routes import charges, refunds, webhooks
from travel_common.config import load_service_config

config = load_service_config("payments-svc")
app = FastAPI(title="payments-svc")
app.include_router(charges.router)
app.include_router(refunds.router)
app.include_router(webhooks.router)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": config.name}
