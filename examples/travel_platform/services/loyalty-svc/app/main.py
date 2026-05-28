from fastapi import FastAPI

from app.routes import accounts, points, redemption
from travel_common.config import load_service_config

config = load_service_config("loyalty-svc")
app = FastAPI(title="loyalty-svc")
app.include_router(accounts.router)
app.include_router(points.router)
app.include_router(redemption.router)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": config.name}
