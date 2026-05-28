"""Centralised logger factory. Every service imports get_logger."""

from __future__ import annotations

import logging
import os
import sys
from typing import Final

_LEVEL: Final[str] = os.environ.get("LOG_LEVEL", "INFO").upper()
_FORMAT: Final[str] = "%(asctime)s %(levelname)s [%(name)s] %(message)s"

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT))
    root = logging.getLogger()
    root.setLevel(_LEVEL)
    root.handlers = [handler]
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger. Safe to call at import time."""
    _configure()
    return logging.getLogger(name)
