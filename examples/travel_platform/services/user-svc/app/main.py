from fastapi import FastAPI

from app.routes import users, profiles, preferences
from travel_common.config import load_service_config

config = load_service_config("user-svc")
app = FastAPI(title="user-svc")
app.include_router(users.router)
app.include_router(profiles.router)
app.include_router(preferences.router)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": config.name}
