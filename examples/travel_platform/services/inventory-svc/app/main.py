from fastapi import FastAPI

from app.routes import inventory, locks, restock
from travel_common.config import load_service_config

config = load_service_config("inventory-svc")
app = FastAPI(title="inventory-svc")
app.include_router(inventory.router)
app.include_router(locks.router)
app.include_router(restock.router)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": config.name}
