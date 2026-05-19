from __future__ import annotations

from typing import Any, Iterable

import networkx as nx

from .models import Edge, EdgeType, Node, NodeType


class GraphStore:
    """NetworkX-backed graph store.

    The public method surface is what MCP tools call. The NetworkX backend
    is hidden so this can be swapped to Memgraph later without changing
    MCP tools or query code.
    """

    def __init__(self) -> None:
        self._graph: nx.MultiDiGraph = nx.MultiDiGraph()

    # ----- mutation -----

    def add_node(self, node: Node) -> None:
        self._graph.add_node(
            node.id,
            type=node.type,
            name=node.name,
            file_path=node.file_path,
            properties=node.properties,
        )

    def add_edge(self, edge: Edge) -> None:
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            key=edge.type.value,
            type=edge.type,
            properties=edge.properties,
        )

    # ----- lookup -----

    def has_node(self, node_id: str) -> bool:
        return node_id in self._graph

    def get_node(self, node_id: str) -> Node | None:
        if node_id not in self._graph:
            return None
        attrs = self._graph.nodes[node_id]
        return Node(
            id=node_id,
            type=attrs["type"],
            name=attrs["name"],
            file_path=attrs["file_path"],
            properties=attrs.get("properties", {}),
        )

    def all_nodes(self) -> list[Node]:
        return [self.get_node(n) for n in self._graph.nodes]  # type: ignore[misc]

    def nodes_by_type(self, node_type: NodeType) -> list[Node]:
        out: list[Node] = []
        for node_id, attrs in self._graph.nodes(data=True):
            if attrs.get("type") == node_type:
                out.append(self.get_node(node_id))  # type: ignore[arg-type]
        return out

    def search_by_name(
        self, query: str, node_types: list[NodeType] | None = None
    ) -> list[Node]:
        q = query.lower()
        out: list[Node] = []
        for node_id, attrs in self._graph.nodes(data=True):
            if node_types and attrs.get("type") not in node_types:
                continue
            name = attrs.get("name", "")
            if q in name.lower():
                out.append(self.get_node(node_id))  # type: ignore[arg-type]
        return out

    # ----- edge queries -----

    def _incoming_edges(
        self, node_id: str, edge_type: EdgeType | None = None
    ) -> Iterable[tuple[str, str, dict]]:
        if node_id not in self._graph:
            return []
        for src, _tgt, data in self._graph.in_edges(node_id, data=True):
            if edge_type is None or data.get("type") == edge_type:
                yield src, node_id, data

    def _outgoing_edges(
        self, node_id: str, edge_type: EdgeType | None = None
    ) -> Iterable[tuple[str, str, dict]]:
        if node_id not in self._graph:
            return []
        for _src, tgt, data in self._graph.out_edges(node_id, data=True):
            if edge_type is None or data.get("type") == edge_type:
                yield node_id, tgt, data

    def get_callers(self, node_id: str, depth: int = 1) -> list[Node]:
        return self._collect_traversal(node_id, EdgeType.CALLS, depth, "in")

    def get_callees(self, node_id: str, depth: int = 1) -> list[Node]:
        return self._collect_traversal(node_id, EdgeType.CALLS, depth, "out")

    def get_imports(self, file_path: str) -> list[Node]:
        return self._collect_traversal(file_path, EdgeType.IMPORTS, 1, "out")

    def get_imported_by(self, file_path: str) -> list[Node]:
        return self._collect_traversal(file_path, EdgeType.IMPORTS, 1, "in")

    def get_file_entities(self, file_path: str) -> list[Node]:
        return self._collect_traversal(file_path, EdgeType.CONTAINS, 1, "out")

    def _collect_traversal(
        self, start: str, edge_type: EdgeType, depth: int, direction: str
    ) -> list[Node]:
        seen: set[str] = set()
        frontier: list[str] = [start]
        for _ in range(depth):
            next_frontier: list[str] = []
            for node_id in frontier:
                edges = (
                    self._incoming_edges(node_id, edge_type)
                    if direction == "in"
                    else self._outgoing_edges(node_id, edge_type)
                )
                for src, tgt, _data in edges:
                    other = src if direction == "in" else tgt
                    if other not in seen and other != start:
                        seen.add(other)
                        next_frontier.append(other)
            frontier = next_frontier
            if not frontier:
                break
        return [n for n in (self.get_node(nid) for nid in seen) if n is not None]

    # ----- analytics -----

    def trace_chain(
        self, from_id: str, direction: str, max_depth: int
    ) -> list[dict[str, Any]]:
        if from_id not in self._graph:
            return []
        chain: list[dict[str, Any]] = []
        seen: set[str] = {from_id}
        frontier: list[tuple[str, str | None]] = [(from_id, None)]
        for depth in range(1, max_depth + 1):
            next_frontier: list[tuple[str, str | None]] = []
            for node_id, _via in frontier:
                edges_in = list(self._incoming_edges(node_id))
                edges_out = list(self._outgoing_edges(node_id))
                if direction == "upstream":
                    candidates = [(s, d) for s, _t, d in edges_in]
                elif direction == "downstream":
                    candidates = [(t, d) for _s, t, d in edges_out]
                else:
                    candidates = [(s, d) for s, _t, d in edges_in] + [
                        (t, d) for _s, t, d in edges_out
                    ]
                for other, data in candidates:
                    if other in seen:
                        continue
                    seen.add(other)
                    other_node = self.get_node(other)
                    if other_node is None:
                        continue
                    edge_type = data.get("type")
                    rel = edge_type.value if isinstance(edge_type, EdgeType) else str(edge_type)
                    chain.append(
                        {
                            "depth": depth,
                            "id": other_node.id,
                            "name": other_node.name,
                            "type": other_node.type.value,
                            "file_path": other_node.file_path,
                            "relationship": rel,
                        }
                    )
                    next_frontier.append((other, rel))
            frontier = next_frontier
            if not frontier:
                break
        return chain

    def impact_analysis(self, node_id: str, max_depth: int = 5) -> dict[str, Any]:
        if node_id not in self._graph:
            return {"target": None, "directly_affected": [], "transitively_affected": [], "affected_files": [], "total_affected": 0, "risk_score": "low", "risk_reason": "Target not found"}

        target = self.get_node(node_id)
        assert target is not None

        # Walk all incoming edges of impact-relevant types.
        impact_edges = {EdgeType.CALLS, EdgeType.IMPORTS, EdgeType.REFERENCES, EdgeType.INHERITS}
        direct: list[dict[str, Any]] = []
        transitive: list[dict[str, Any]] = []
        affected_files: set[str] = set()

        seen: set[str] = {node_id}
        frontier: list[tuple[str, int]] = [(node_id, 0)]
        while frontier:
            current, depth = frontier.pop(0)
            if depth >= max_depth:
                continue
            for src, _tgt, data in self._incoming_edges(current):
                edge_type = data.get("type")
                if edge_type not in impact_edges:
                    continue
                if src in seen:
                    continue
                seen.add(src)
                src_node = self.get_node(src)
                if src_node is None:
                    continue
                affected_files.add(src_node.file_path)
                entry = {
                    "id": src_node.id,
                    "name": src_node.name,
                    "type": src_node.type.value,
                    "file_path": src_node.file_path,
                    "relationship": edge_type.value if isinstance(edge_type, EdgeType) else str(edge_type),
                    "depth": depth + 1,
                }
                if depth == 0:
                    direct.append(entry)
                else:
                    transitive.append(entry)
                frontier.append((src, depth + 1))

        total = len(direct) + len(transitive)
        if total >= 15:
            risk = "high"
            reason = f"Widely used: {len(direct)} direct + {len(transitive)} transitive dependents"
        elif total >= 5:
            risk = "medium"
            reason = f"{len(direct)} direct callers across {len(affected_files)} files"
        else:
            risk = "low"
            reason = f"Limited use: {len(direct)} direct dependents"

        return {
            "target": target.to_dict(),
            "directly_affected": direct,
            "transitively_affected": transitive,
            "affected_files": sorted(affected_files),
            "total_affected": total,
            "risk_score": risk,
            "risk_reason": reason,
        }

    def find_hotspots(self, top_n: int = 10) -> list[dict[str, Any]]:
        scored: list[tuple[int, int, int, str]] = []
        for node_id, attrs in self._graph.nodes(data=True):
            if attrs.get("type") not in (NodeType.FUNCTION, NodeType.CLASS):
                continue
            callers = sum(
                1 for _ in self._incoming_edges(node_id, EdgeType.CALLS)
            )
            callees = sum(
                1 for _ in self._outgoing_edges(node_id, EdgeType.CALLS)
            )
            inherits_in = sum(
                1 for _ in self._incoming_edges(node_id, EdgeType.INHERITS)
            )
            total = callers + callees + inherits_in
            scored.append((total, callers, callees, node_id))

        scored.sort(reverse=True)
        out: list[dict[str, Any]] = []
        for total, callers, callees, node_id in scored[:top_n]:
            node = self.get_node(node_id)
            if node is None:
                continue
            if total == 0:
                continue
            risk = (
                "very high — likely single point of failure"
                if callers >= 10
                else "high — heavily depended on"
                if callers >= 5
                else "moderate"
            )
            out.append(
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.type.value,
                    "file_path": node.file_path,
                    "callers": callers,
                    "callees": callees,
                    "total_connections": total,
                    "risk": risk,
                }
            )
        return out

    def find_orphans(self) -> list[Node]:
        """Functions and classes with no incoming CALLS/REFERENCES/INHERITS edges.

        Filters out test functions, dunder methods, and common entry points.
        """
        out: list[Node] = []
        for node_id, attrs in self._graph.nodes(data=True):
            ntype = attrs.get("type")
            if ntype not in (NodeType.FUNCTION, NodeType.CLASS):
                continue
            name = attrs.get("name", "")
            props = attrs.get("properties", {})
            if name.startswith("test_") or name.startswith("__"):
                continue
            if name in {"main", "create_app", "app", "handler", "index"}:
                continue
            if props.get("is_nested"):
                continue
            in_edges = list(self._graph.in_edges(node_id, data=True))
            non_contains = [
                d for _s, _t, d in in_edges if d.get("type") != EdgeType.CONTAINS
            ]
            if not non_contains:
                node = self.get_node(node_id)
                if node is not None:
                    out.append(node)
        return out

    def find_cycles(self, max_length: int = 6) -> list[list[str]]:
        # File-level import cycles
        subgraph = nx.DiGraph()
        for src, tgt, data in self._graph.edges(data=True):
            if data.get("type") == EdgeType.IMPORTS:
                subgraph.add_edge(src, tgt)
        cycles: list[list[str]] = []
        try:
            for cycle in nx.simple_cycles(subgraph):
                if len(cycle) <= max_length:
                    cycles.append(cycle + [cycle[0]])
        except nx.NetworkXNoCycle:
            pass
        return cycles

    # ----- stats -----

    def stats(self) -> dict[str, Any]:
        files = sum(1 for _, a in self._graph.nodes(data=True) if a.get("type") == NodeType.FILE)
        funcs = sum(1 for _, a in self._graph.nodes(data=True) if a.get("type") == NodeType.FUNCTION)
        classes = sum(1 for _, a in self._graph.nodes(data=True) if a.get("type") == NodeType.CLASS)
        types = sum(1 for _, a in self._graph.nodes(data=True) if a.get("type") == NodeType.TYPE)
        edges = self._graph.number_of_edges()
        return {
            "files": files,
            "functions": funcs,
            "classes": classes,
            "types": types,
            "edges": edges,
            "total_nodes": self._graph.number_of_nodes(),
        }
