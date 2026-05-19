from __future__ import annotations

from pathlib import Path

import pytest

from unlearn.graph import (
    find_circular_dependencies,
    find_dead_code,
    find_hotspots,
    get_context,
    impact_analysis,
    trace_dependencies,
)
from unlearn.indexer import index_repo


@pytest.fixture
def py_store(python_simple_root: Path):
    return index_repo(python_simple_root).store


@pytest.fixture
def ts_store(typescript_simple_root: Path):
    return index_repo(typescript_simple_root).store


def test_impact_analysis_validate_token_finds_route_handlers(py_store):
    result = impact_analysis(py_store, "validate_token")
    affected_files = set(result["affected_files"])
    assert "auth/middleware.py" in affected_files
    # And via middleware.decorated → ... (the route functions are wrapped by
    # auth_required, but validate_token is only directly called from middleware)
    affected_names = {entry["name"] for entry in result["directly_affected"]}
    assert "decorated" in affected_names


def test_impact_analysis_unknown_entity(py_store):
    result = impact_analysis(py_store, "no_such_thing")
    assert "error" in result


def test_trace_dependencies_downstream(py_store):
    result = trace_dependencies(py_store, "create_payment_endpoint", direction="downstream", max_depth=5)
    chain_names = {entry["name"] for entry in result["chain"]}
    # create_payment_endpoint → charge_customer → get_or_create_stripe_customer
    assert "charge_customer" in chain_names
    assert "get_or_create_stripe_customer" in chain_names


def test_find_hotspots(py_store):
    result = find_hotspots(py_store, top_n=5)
    names = [h["name"] for h in result["hotspots"]]
    # User class and auth_required should be high on the list.
    assert "User" in names or "auth_required" in names


def test_find_dead_code_finds_deprecated(py_store):
    result = find_dead_code(py_store)
    dead_names = {item["name"] for item in result["dead_code"]}
    assert "old_token_validator" in dead_names
    assert "legacy_hash" in dead_names
    assert "unused_helper" in dead_names
    # Should NOT flag route handlers (imported by app.py).
    assert "get_user" not in dead_names
    assert "create_payment_endpoint" not in dead_names


def test_find_dead_code_ts(ts_store):
    result = find_dead_code(ts_store)
    dead_names = {item["name"] for item in result["dead_code"]}
    assert "legacyParser" in dead_names
    assert "legacyFormatter" in dead_names
    # Route handlers should NOT be flagged.
    assert "getUser" not in dead_names


def test_find_circular_dependencies_ts(ts_store):
    result = find_circular_dependencies(ts_store)
    assert result["total_cycles"] >= 1
    # Confirm one cycle involves middleware↔roles.
    found = False
    for cycle in result["cycles"]:
        files = set(cycle["chain"])
        if {"src/auth/middleware.ts", "src/auth/roles.ts"}.issubset(files):
            found = True
    assert found


def test_get_context_for_function(py_store):
    result = get_context(py_store, "validate_token")
    assert result["target"]["name"] == "validate_token"
    caller_names = {c["name"] for c in result["callers"]}
    callee_names = {c["name"] for c in result["callees"]}
    assert "decoded_payload" not in callee_names  # sanity
    assert "decode_payload" in callee_names
    assert "verify_signature" in callee_names
    assert "decorated" in caller_names  # called from middleware


def test_get_context_for_file(py_store):
    result = get_context(py_store, "auth/jwt.py")
    entity_names = {e["name"] for e in result["entities"]}
    assert "validate_token" in entity_names
    assert "generate_token" in entity_names
