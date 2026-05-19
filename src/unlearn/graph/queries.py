"""Higher-level graph queries that compose GraphStore primitives.

These power the MCP tools. They return plain JSON-serialisable dicts.
"""
from __future__ import annotations

from typing import Any

from .models import EdgeType, Node, NodeType
from .store import GraphStore


def _node_dict(n: Node) -> dict[str, Any]:
    return {
        "id": n.id,
        "name": n.name,
        "type": n.type.value,
        "file_path": n.file_path,
        "line_start": n.properties.get("line_start"),
        "line_end": n.properties.get("line_end"),
    }


def _find_targets(store: GraphStore, entity: str) -> list[Node]:
    """Find graph nodes matching `entity` — accepts exact id, exact name, or substring."""
    # 1) Exact node id.
    node = store.get_node(entity)
    if node is not None:
        return [node]
    # 2) Exact name match (any type except File).
    name_matches: list[Node] = []
    for n in store.all_nodes():
        if n.type == NodeType.FILE:
            continue
        if n.name == entity:
            name_matches.append(n)
    if name_matches:
        return name_matches
    # 3) File path match.
    file_node = store.get_node(entity)
    if file_node is not None:
        return [file_node]
    for n in store.all_nodes():
        if n.type == NodeType.FILE and n.file_path == entity:
            return [n]
    # 4) Substring search (last resort).
    return store.search_by_name(entity)


def impact_analysis(
    store: GraphStore, entity: str, change_type: str = "modify", max_depth: int = 5
) -> dict[str, Any]:
    targets = _find_targets(store, entity)
    if not targets:
        return {
            "query": entity,
            "matches": 0,
            "error": f"No entity found matching {entity!r}",
        }

    # If multiple matches, aggregate.
    aggregated: dict[str, Any] = {
        "query": entity,
        "change_type": change_type,
        "matches": len(targets),
        "results": [],
    }
    for target in targets:
        result = store.impact_analysis(target.id, max_depth=max_depth)
        aggregated["results"].append(result)
    # Convenience: if exactly one match, lift its fields to the top.
    if len(aggregated["results"]) == 1:
        single = aggregated["results"][0]
        aggregated.update(
            {
                "target": single["target"],
                "directly_affected": single["directly_affected"],
                "transitively_affected": single["transitively_affected"],
                "affected_files": single["affected_files"],
                "total_affected": single["total_affected"],
                "risk_score": single["risk_score"],
                "risk_reason": single["risk_reason"],
            }
        )
    return aggregated


def trace_dependencies(
    store: GraphStore,
    entity: str,
    direction: str = "downstream",
    max_depth: int = 8,
) -> dict[str, Any]:
    targets = _find_targets(store, entity)
    if not targets:
        return {"query": entity, "error": f"No entity found matching {entity!r}"}
    target = targets[0]
    chain = store.trace_chain(target.id, direction=direction, max_depth=max_depth)
    affected_files = sorted({entry["file_path"] for entry in chain})
    total_depth = max((entry["depth"] for entry in chain), default=0)
    return {
        "target": _node_dict(target),
        "direction": direction,
        "chain": chain,
        "total_depth": total_depth,
        "affected_files": affected_files,
        "ambiguous_matches": [_node_dict(t) for t in targets[1:]],
    }


def find_hotspots(store: GraphStore, top_n: int = 10) -> dict[str, Any]:
    return {"hotspots": store.find_hotspots(top_n=top_n)}


def find_dead_code(store: GraphStore) -> dict[str, Any]:
    orphans = store.find_orphans()
    dead = [
        {
            "id": n.id,
            "name": n.name,
            "type": n.type.value,
            "file_path": n.file_path,
            "line_start": n.properties.get("line_start"),
        }
        for n in orphans
    ]
    return {
        "dead_code": dead,
        "total_dead": len(dead),
        "note": "Excludes test functions, dunder methods, and common entry points (main, handler, index, etc.)",
    }


def find_circular_dependencies(
    store: GraphStore, max_cycle_length: int = 6
) -> dict[str, Any]:
    cycles_raw = store.find_cycles(max_length=max_cycle_length)
    cycles = [{"chain": c, "length": len(c) - 1} for c in cycles_raw]
    return {"cycles": cycles, "total_cycles": len(cycles)}


def get_context(store: GraphStore, entity: str, depth: int = 1) -> dict[str, Any]:
    targets = _find_targets(store, entity)
    if not targets:
        return {"query": entity, "error": f"No entity found matching {entity!r}"}
    target = targets[0]

    if target.type == NodeType.FILE:
        return _file_context(store, target)
    return _entity_context(store, target, depth=depth)


def _entity_context(store: GraphStore, target: Node, depth: int) -> dict[str, Any]:
    callers = [_node_dict(n) for n in store.get_callers(target.id, depth=depth)]
    callees = [_node_dict(n) for n in store.get_callees(target.id, depth=depth)]

    # Siblings: other entities in the same file.
    file_entities = store.get_file_entities(target.file_path)
    siblings = [
        _node_dict(n) for n in file_entities if n.id != target.id
    ]

    imports = [_node_dict(n) for n in store.get_imports(target.file_path)]
    imported_by = [_node_dict(n) for n in store.get_imported_by(target.file_path)]

    return {
        "target": {
            **_node_dict(target),
            "properties": target.properties,
        },
        "callers": callers,
        "callees": callees,
        "imported_by": imported_by,
        "imports": imports,
        "siblings": siblings,
    }


def _file_context(store: GraphStore, target: Node) -> dict[str, Any]:
    entities = [_node_dict(n) for n in store.get_file_entities(target.file_path)]
    imports = [_node_dict(n) for n in store.get_imports(target.file_path)]
    imported_by = [_node_dict(n) for n in store.get_imported_by(target.file_path)]
    return {
        "target": {**_node_dict(target), "properties": target.properties},
        "entities": entities,
        "imports": imports,
        "imported_by": imported_by,
    }


def search(
    store: GraphStore, query: str, types: list[str] | None = None
) -> dict[str, Any]:
    node_types = (
        [NodeType(t) for t in types] if types else None
    )
    matches = store.search_by_name(query, node_types=node_types)
    return {
        "query": query,
        "matches": [_node_dict(n) for n in matches],
        "total": len(matches),
    }
