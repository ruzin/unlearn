from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def stopwatch() -> Iterator[dict[str, float]]:
    """Context manager that records elapsed milliseconds in `result['ms']`."""
    result: dict[str, float] = {"ms": 0.0}
    start = time.perf_counter()
    try:
        yield result
    finally:
        result["ms"] = (time.perf_counter() - start) * 1000.0
