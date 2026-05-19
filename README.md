# Unlearn

Codebase knowledge graph for AI agents. Indexes your repo into a structural graph (functions, classes, imports, calls, inheritance) and exposes it over MCP so Claude Code can answer questions like *"what breaks if I change X?"* with complete, deterministic, millisecond answers — instead of grepping files and guessing.

## What's in v0.1

- **Languages:** Python, TypeScript, JavaScript (incl. TSX)
- **Graph:** In-memory NetworkX (no Docker). Swappable for Memgraph later.
- **Transport:** MCP over stdio (for Claude Code).
- **Cache:** `.unlearn/graph.json` for fast reloads.

## Quick start

```bash
uv sync                                  # install deps
uv run unlearn index .                   # index the current repo
uv run unlearn info .                    # show graph stats
uv run unlearn serve .                   # start the MCP server (stdio)
```

## Hook up to Claude Code

Add this to a `.mcp.json` at the root of any repo you've indexed:

```json
{
  "mcpServers": {
    "unlearn": {
      "command": "uv",
      "args": ["run", "unlearn", "serve", "."]
    }
  }
}
```

Claude Code auto-discovers `.mcp.json` and launches the server on startup. Once connected, it has eight tools available:

| Tool                          | Use it when…                                                  |
|-------------------------------|---------------------------------------------------------------|
| `impact_analysis`             | "What breaks if I change/delete/rename X?"                    |
| `trace_dependencies`          | "Show me the call chain from A to B."                         |
| `find_hotspots`               | "What are the most critical functions?"                       |
| `find_dead_code`              | "What code is never called?"                                  |
| `find_circular_dependencies`  | "Are there any import cycles?"                                |
| `get_context`                 | "Tell me everything connected to function X."                 |
| `search_entities`             | Fuzzy name search across files/functions/classes/types.       |
| `graph_stats`                 | Cache metadata, node/edge counts.                             |

## Why bother

Claude Code reads files. It can answer structural questions, but only by *grepping then guessing* — slow, incomplete, and unreliable for impact analysis or transitive dependency tracing. The graph gives you:

- **Complete**: every caller, every transitive importer, no missed sites.
- **Deterministic**: the same query returns the same answer every time.
- **Fast**: graph traversal is sub-millisecond once indexed.

## How it works

```
CLI (click)
   └─→ Indexer
         ├─ walk repo, skip .git/node_modules/etc.
         ├─ tree-sitter AST per file (Python / TS / JS)
         ├─ per-file extraction: functions, classes, imports, calls, decorators, inheritance
         └─ resolver pass: stitch imports → cross-file CALLS/REFERENCES/INHERITS edges
   ↓
GraphStore (NetworkX DiGraph)
   ├─ node types: File, Function, Class, Type
   ├─ edge types: CONTAINS, CALLS, IMPORTS, INHERITS, REFERENCES
   ├─ queries: impact, trace, hotspots, dead code, cycles, context
   └─ JSON serialisation → .unlearn/graph.json
   ↓
MCP server (FastMCP, stdio)
   └─ 8 tools wrap the graph queries
```

## Layout

```
src/unlearn/
├── cli.py                       click CLI entry
├── indexer/
│   ├── pipeline.py              orchestrator
│   ├── languages.py             tree-sitter language registry
│   ├── resolver.py              import + call resolution
│   └── extractors/
│       ├── base.py              shared dataclasses + protocol
│       ├── common.py            tree-sitter helpers
│       ├── python.py            Python extractor
│       └── typescript.py        TypeScript/JavaScript extractor
├── graph/
│   ├── models.py                Node / Edge / NodeType / EdgeType
│   ├── store.py                 GraphStore (NetworkX backend)
│   ├── queries.py               impact_analysis, trace, hotspots, …
│   └── serialise.py             JSON cache
├── mcp/
│   └── server.py                FastMCP server + tool definitions
└── utils/
    ├── files.py                 repo walking + ignore list
    └── timing.py                stopwatch
tests/
├── fixtures/
│   ├── python_simple/           ~15-file Python repo (Flask-ish)
│   └── typescript_simple/       ~12-file TS repo (Express-ish, with cycle + dead code)
├── test_extractors.py
├── test_graph.py
├── test_queries.py
├── test_mcp_tools.py
└── test_integration.py
scripts/
└── benchmark.py                 run the spec's structural queries against a repo
```

## Limitations (v0.1)

These are deliberately deferred — see `UNLEARN_FULL_SPEC.md` for the longer roadmap.

- **No Docker / Memgraph yet.** NetworkX in-memory is fine for repos up to ~50k files.
- **No embeddings / semantic search.** Search is substring-based.
- **No LLM enrichment.** Pure structural extraction.
- **stdio only.** No HTTP transport.
- **Python + TS/JS only.** Go, Rust, Java come later.
- **Single repo.** Cross-repo comes later.
- **Full re-index every time.** No incremental updates yet.

## Development

```bash
uv sync --extra dev                # install pytest
uv run pytest                       # run all tests
uv run pytest tests/test_queries.py # one file
uv run python scripts/benchmark.py tests/fixtures/python_simple  # run benchmark
```

Tests live alongside two small fixture repos. The Python fixture is a Flask-ish API; the TypeScript fixture is an Express-ish app with an intentional `middleware ↔ roles` import cycle and an unused `legacy.ts` for dead-code testing.

## Spec

The full build spec is in `UNLEARN_V01_SPEC.md`; the longer-term plan is in `UNLEARN_FULL_SPEC.md`.
