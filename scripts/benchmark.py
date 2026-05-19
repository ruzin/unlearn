"""Run the benchmark queries from UNLEARN_V01_SPEC.md against a repo.

Usage:
    uv run python scripts/benchmark.py [repo_path]

Indexes the repo, then runs each structural query against the graph and prints
a compact summary. Useful as a smoke test and as a side-by-side reference for
asking Claude Code the same questions (with and without Unlearn).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from unlearn.graph import (
    find_circular_dependencies,
    find_dead_code,
    find_hotspots,
    get_context,
    impact_analysis,
    trace_dependencies,
)
from unlearn.indexer import index_repo


BENCHMARK_QUERIES = [
    {
        "id": "impact_1",
        "title": "Impact: what breaks if we delete validate_token?",
        "run": lambda store: impact_analysis(store, "validate_token", change_type="delete"),
    },
    {
        "id": "trace_1",
        "title": "Trace: full chain from create_payment_endpoint",
        "run": lambda store: trace_dependencies(store, "create_payment_endpoint", direction="downstream", max_depth=6),
    },
    {
        "id": "hotspot_1",
        "title": "Hotspots: most critical functions",
        "run": lambda store: find_hotspots(store, top_n=5),
    },
    {
        "id": "dead_1",
        "title": "Dead code",
        "run": lambda store: find_dead_code(store),
    },
    {
        "id": "circular_1",
        "title": "Circular dependencies",
        "run": lambda store: find_circular_dependencies(store),
    },
    {
        "id": "context_1",
        "title": "Context: User model",
        "run": lambda store: get_context(store, "User"),
    },
]


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    print(f"Indexing {root} ...")
    result = index_repo(root)
    print(
        f"  {result.files_indexed} files, "
        f"{result.store.stats()['functions']} functions, "
        f"{result.store.stats()['edges']} edges, "
        f"{result.elapsed_ms:.0f} ms"
    )
    print()

    for q in BENCHMARK_QUERIES:
        print(f"--- [{q['id']}] {q['title']}")
        try:
            output = q["run"](result.store)
        except Exception as exc:  # pragma: no cover
            print(f"  ERROR: {exc}")
            continue
        print(json.dumps(_summarise(output), indent=2))
        print()
    return 0


def _summarise(out: dict) -> dict:
    """Trim verbose fields for terminal readability."""
    if isinstance(out, dict):
        return {k: _trim(v) for k, v in out.items()}
    return out


def _trim(v):
    if isinstance(v, list) and len(v) > 8:
        return v[:8] + [f"... ({len(v) - 8} more)"]
    if isinstance(v, dict):
        return {k: _trim(vv) for k, vv in v.items()}
    return v


if __name__ == "__main__":
    sys.exit(main(sys.argv))
