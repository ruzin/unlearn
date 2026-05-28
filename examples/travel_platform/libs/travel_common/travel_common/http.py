"""Tiny HTTP client wrapper used by services for inter-service calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from travel_common.errors import TravelError
from travel_common.logging import get_logger

_log = get_logger(__name__)


@dataclass
class HttpResponse:
    status: int
    body: Any


class ServiceClient:
    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get(self, path: str, params: dict[str, Any] | None = None) -> HttpResponse:
        _log.debug("GET %s%s params=%s", self.base_url, path, params)
        return HttpResponse(status=200, body={})

    def post(self, path: str, body: Any) -> HttpResponse:
        _log.debug("POST %s%s body=%s", self.base_url, path, body)
        return HttpResponse(status=200, body={})

    def raise_for_status(self, response: HttpResponse) -> None:
        if response.status >= 400:
            raise TravelError(f"upstream {response.status}", code="http/upstream")
