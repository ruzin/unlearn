from __future__ import annotations

from pathlib import Path

from unlearn.graph.models import EdgeType, NodeType
from unlearn.indexer import index_repo


def test_python_graph_has_expected_shape(python_simple_root: Path):
    result = index_repo(python_simple_root)
    stats = result.store.stats()
    assert stats["files"] >= 10
    assert stats["functions"] >= 25
    assert stats["classes"] == 2  # User, Payment


def test_python_call_edges_resolved(python_simple_root: Path):
    store = index_repo(python_simple_root).store
    # validate_token in jwt.py should have decorated() as a caller.
    callers = {n.name for n in store.get_callers("auth/jwt.py::validate_token::8")}
    assert "decorated" in callers


def test_python_import_edges_resolved(python_simple_root: Path):
    store = index_repo(python_simple_root).store
    imports = {n.file_path for n in store.get_imports("routes/users.py")}
    assert "auth/middleware.py" in imports
    assert "models/user.py" in imports


def test_python_decorator_creates_calls_edge(python_simple_root: Path):
    store = index_repo(python_simple_root).store
    # routes/users.get_user is decorated with auth_required, so it should
    # have a CALLS edge to auth_required.
    callees = {n.name for n in store.get_callees("routes/users.py::get_user::6")}
    assert "auth_required" in callees


def test_typescript_circular_import(typescript_simple_root: Path):
    store = index_repo(typescript_simple_root).store
    cycles = store.find_cycles(max_length=4)
    # Expect cycle between middleware.ts and roles.ts
    found = False
    for cycle in cycles:
        names = {c for c in cycle}
        if "src/auth/middleware.ts" in names and "src/auth/roles.ts" in names:
            found = True
    assert found, f"expected middleware↔roles cycle, got: {cycles}"


def test_serialise_roundtrip(python_simple_root: Path, tmp_path: Path):
    from unlearn.graph.serialise import load_from_disk, save_to_disk

    result = index_repo(python_simple_root)
    cache = tmp_path / "graph.json"
    save_to_disk(result.store, str(python_simple_root), cache)
    loaded, _ = load_from_disk(cache)
    assert loaded.stats() == result.store.stats()
    assert {n.id for n in loaded.all_nodes()} == {n.id for n in result.store.all_nodes()}


def test_node_types_and_edge_types_distinct(python_simple_root: Path):
    store = index_repo(python_simple_root).store
    nodes = store.all_nodes()
    types = {n.type for n in nodes}
    assert NodeType.FILE in types
    assert NodeType.FUNCTION in types
    assert NodeType.CLASS in types

    edge_types = {data["type"] for _s, _t, data in store._graph.edges(data=True)}
    assert EdgeType.CONTAINS in edge_types
    assert EdgeType.CALLS in edge_types
    assert EdgeType.IMPORTS in edge_types
    assert EdgeType.REFERENCES in edge_types
