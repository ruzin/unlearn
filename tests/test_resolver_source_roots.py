"""Source-root detection for Python imports across monorepo layouts."""
from __future__ import annotations

from unlearn.indexer.extractors.base import ImportStatement
from unlearn.indexer.resolver import (
    compute_python_source_roots,
    resolve_python_import,
)


def _abs_import(module: str, names: list[str]) -> ImportStatement:
    return ImportStatement(
        module=module,
        imported_names=names,
        alias=None,
        is_relative=False,
        relative_level=0,
        line=1,
    )


def test_flat_layout_uses_indexed_root():
    """python_simple-style: __init__.py directly under root."""
    known = {
        "auth/__init__.py",
        "auth/jwt.py",
        "models/user.py",
        "app.py",
    }
    roots = compute_python_source_roots(known)
    assert "" in roots
    # auth/__init__.py exists but its parent ("") has no __init__.py -> "" is the root.
    assert roots == [""]


def test_monorepo_layout_detects_per_package_roots():
    """travel_platform-style: services/<svc>/app/ and libs/<pkg>/<pkg>/."""
    known = {
        "libs/travel_common/travel_common/__init__.py",
        "libs/travel_common/travel_common/currency.py",
        "services/booking-svc/app/__init__.py",
        "services/booking-svc/app/handlers/__init__.py",
        "services/booking-svc/app/handlers/create.py",
        "services/pricing-svc/app/__init__.py",
        "services/pricing-svc/app/services/__init__.py",
        "services/pricing-svc/app/services/pricing.py",
    }
    roots = compute_python_source_roots(known)
    # Indexed root always included.
    assert "" in roots
    # Each service-level dir is a source root.
    assert "libs/travel_common" in roots
    assert "services/booking-svc" in roots
    assert "services/pricing-svc" in roots


def test_resolve_cross_package_import():
    """Importing travel_common.currency from a service should land on libs/.../currency.py."""
    known = {
        "libs/travel_common/travel_common/__init__.py",
        "libs/travel_common/travel_common/currency.py",
        "services/pricing-svc/app/__init__.py",
        "services/pricing-svc/app/services/__init__.py",
        "services/pricing-svc/app/services/pricing.py",
    }
    roots = compute_python_source_roots(known)
    stmt = _abs_import("travel_common.currency", ["format_currency"])
    target = resolve_python_import(
        "services/pricing-svc/app/services/pricing.py", stmt, known, roots
    )
    assert target == "libs/travel_common/travel_common/currency.py"


def test_resolve_intra_package_absolute_import():
    """Within a service: `from app.services.taxes import compute_tax`."""
    known = {
        "services/pricing-svc/app/__init__.py",
        "services/pricing-svc/app/services/__init__.py",
        "services/pricing-svc/app/services/pricing.py",
        "services/pricing-svc/app/services/taxes.py",
    }
    roots = compute_python_source_roots(known)
    stmt = _abs_import("app.services.taxes", ["compute_tax"])
    target = resolve_python_import(
        "services/pricing-svc/app/services/pricing.py", stmt, known, roots
    )
    assert target == "services/pricing-svc/app/services/taxes.py"


def test_flat_layout_absolute_import_still_resolves():
    """Regression: python_simple's `from auth.jwt import validate_token` must still work."""
    known = {
        "auth/__init__.py",
        "auth/jwt.py",
        "auth/middleware.py",
    }
    roots = compute_python_source_roots(known)
    stmt = _abs_import("auth.jwt", ["validate_token"])
    target = resolve_python_import("auth/middleware.py", stmt, known, roots)
    assert target == "auth/jwt.py"
