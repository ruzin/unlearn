"""Common config-loading helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceConfig:
    name: str
    env: str
    region: str
    debug: bool


def load_service_config(name: str) -> ServiceConfig:
    return ServiceConfig(
        name=name,
        env=os.environ.get("TRAVEL_ENV", "dev"),
        region=os.environ.get("AWS_REGION", "us-east-1"),
        debug=os.environ.get("DEBUG", "0") == "1",
    )
