"""MCP server exposing the graph queries as tools.

Runs over stdio. The graph is loaded from `.unlearn/graph.json` at startup if
present; otherwise the server indexes the working directory first.
"""
from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ..graph import (
    GraphStore,
    find_circular_dependencies,
    find_dead_code,
    find_hotspots,
    get_context,
    impact_analysis,
    search,
    trace_dependencies,
)
from ..graph.serialise import load_from_disk
from ..indexer import index_repo


CACHE_RELATIVE = Path(".unlearn") / "graph.json"


def _load_graph(root: Path) -> tuple[GraphStore, dict]:
    cache_path = root / CACHE_RELATIVE
    if cache_path.exists():
        store, payload = load_from_disk(cache_path)
        return store, {"source": "cache", "indexed_at": payload.get("indexed_at"), "root": payload.get("root")}
    result = index_repo(root)
    return result.store, {
        "source": "fresh",
        "indexed_at": None,
        "root": str(root),
        "files_indexed": result.files_indexed,
        "elapsed_ms": result.elapsed_ms,
    }


def build_server(root: Path) -> FastMCP:
    store, meta = _load_graph(root.resolve())

    mcp: FastMCP = FastMCP("unlearn")

    @mcp.tool(name="impact_analysis")
    def impact_analysis_tool(
        entity: str, change_type: str = "modify", max_depth: int = 5
    ) -> dict:
        """Analyse the downstream impact of changing a code entity.

        Returns all directly and transitively affected functions, classes, and
        files — with depth information and risk assessment.

        Use this when: the user asks what would break if they change, delete,
        rename, or refactor something.
        """
        return impact_analysis(store, entity, change_type=change_type, max_depth=max_depth)

    @mcp.tool(name="trace_dependencies")
    def trace_dependencies_tool(
        entity: str, direction: str = "downstream", max_depth: int = 8
    ) -> dict:
        """Trace the full dependency chain from a code entity.

        `direction`: "upstream" (callers), "downstream" (callees), "both".

        Use this when: the user asks about call chains, request flows, data
        flows, or wants to understand how deep a dependency goes.
        """
        return trace_dependencies(store, entity, direction=direction, max_depth=max_depth)

    @mcp.tool(name="find_hotspots")
    def find_hotspots_tool(top_n: int = 10) -> dict:
        """Find the most connected and most critical code entities in the codebase.

        Ranks by total connections (callers + callees).

        Use this when: the user asks about critical code, high-risk functions,
        most important parts of the codebase, or where to focus testing.
        """
        return find_hotspots(store, top_n=top_n)

    @mcp.tool(name="find_dead_code")
    def find_dead_code_tool() -> dict:
        """Find exported functions and classes that have zero callers and are
        not entry points, test functions, or lifecycle hooks.

        Use this when: the user asks about dead code, unused functions,
        cleanup opportunities, or code they can safely delete.
        """
        return find_dead_code(store)

    @mcp.tool(name="find_circular_dependencies")
    def find_circular_dependencies_tool(max_cycle_length: int = 6) -> dict:
        """Detect circular dependency chains in module imports.

        Use this when: the user asks about circular dependencies, import
        cycles, or architectural issues in the codebase.
        """
        return find_circular_dependencies(store, max_cycle_length=max_cycle_length)

    @mcp.tool(name="get_context")
    def get_context_tool(entity: str, depth: int = 1) -> dict:
        """Get the full graph context for a code entity — what it is, what
        calls it, what it calls, what types it uses, and its siblings.

        Use this when: the user asks about a specific function, class, or file
        and you want complete structural context to give a thorough answer.
        """
        return get_context(store, entity, depth=depth)

    @mcp.tool(name="search_entities")
    def search_entities_tool(query: str, types: list[str] | None = None) -> dict:
        """Search for entities by substring of name. Optionally filter by
        type: File, Function, Class, Type.
        """
        return search(store, query, types=types)

    @mcp.tool(name="graph_stats")
    def graph_stats_tool() -> dict:
        """Return stats about the loaded graph: node/edge counts, source."""
        return {"stats": store.stats(), "meta": meta}

    return mcp


def run_stdio(root: Path) -> None:
    server = build_server(root)
    server.run("stdio")
