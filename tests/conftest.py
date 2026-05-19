from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def python_simple_root() -> Path:
    return FIXTURES_DIR / "python_simple"


@pytest.fixture
def typescript_simple_root() -> Path:
    return FIXTURES_DIR / "typescript_simple"
