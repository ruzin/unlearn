from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Edge, EdgeType, Node, NodeType
from .store import GraphStore

CACHE_VERSION = "0.1"


def graph_to_json(store: GraphStore, root: str) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    for node_id, attrs in store._graph.nodes(data=True):  # noqa: SLF001
        ntype = attrs["type"]
        nodes.append(
            {
                "id": node_id,
                "type": ntype.value if isinstance(ntype, NodeType) else ntype,
                "name": attrs["name"],
                "file_path": attrs["file_path"],
                "properties": attrs.get("properties", {}),
            }
        )
    edges: list[dict[str, Any]] = []
    for src, tgt, data in store._graph.edges(data=True):  # noqa: SLF001
        etype = data["type"]
        edges.append(
            {
                "source": src,
                "target": tgt,
                "type": etype.value if isinstance(etype, EdgeType) else etype,
                "properties": data.get("properties", {}),
            }
        )
    return {
        "version": CACHE_VERSION,
        "indexed_at": datetime.now(timezone.utc).isoformat(),
        "root": root,
        "stats": store.stats(),
        "nodes": nodes,
        "edges": edges,
    }


def graph_from_json(data: dict[str, Any]) -> GraphStore:
    store = GraphStore()
    for n in data.get("nodes", []):
        store.add_node(Node.from_dict(n))
    for e in data.get("edges", []):
        store.add_edge(Edge.from_dict(e))
    return store


def save_to_disk(store: GraphStore, root: str, cache_path: Path) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = graph_to_json(store, root)
    cache_path.write_text(json.dumps(payload, indent=2))


def load_from_disk(cache_path: Path) -> tuple[GraphStore, dict[str, Any]]:
    data = json.loads(cache_path.read_text())
    return graph_from_json(data), data
