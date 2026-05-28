from fastapi import FastAPI

from app.routes import flights, hotels, packages
from travel_common.config import load_service_config

config = load_service_config("search-svc")
app = FastAPI(title="search-svc")
app.include_router(flights.router)
app.include_router(hotels.router)
app.include_router(packages.router)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": config.name}
