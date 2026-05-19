# CLAUDE.md — Unlearn

## Project

Unlearn is a CLI tool that indexes code repositories into an in-memory graph (NetworkX), then exposes structural queries via an MCP server. The graph captures functions, classes, types, imports, and call relationships. Claude Code (or any MCP client) calls the tools to answer structural questions that LLMs can't reliably do by reading files: impact analysis, dependency tracing, hotspot detection, dead code, circular dependencies.

## Tech Stack

- Python 3.11+, managed with `uv`
- tree-sitter for AST parsing (Python + TypeScript/JavaScript)
- NetworkX for in-memory directed graph
- FastMCP for MCP server (stdio transport)
- click for CLI
- pytest for tests

## Commands

```bash
uv sync                              # install dependencies
uv run pytest                        # run all tests
uv run pytest tests/test_extractors.py  # run specific test file
uv run unlearn index [path]          # index a repo
uv run unlearn serve                 # start MCP server (stdio)
uv run unlearn info [path]           # show graph stats
```

## Architecture

```
CLI (click) → Indexer (tree-sitter) → GraphStore (NetworkX) → MCP Server (FastMCP)
                                            ↕
                                    .unlearn/graph.json (cache)
```

- `src/unlearn/indexer/` — file discovery, AST extraction per language, import/call resolution
- `src/unlearn/graph/` — NetworkX graph wrapper, node/edge models, query methods
- `src/unlearn/mcp/` — FastMCP server, 8 tool definitions that call graph queries (6 from spec + `search_entities` and `graph_stats`)
- `tests/fixtures/` — small test repos (python_simple, typescript_simple)

## Code Style

- Type hints on all function signatures
- Dataclasses for Node, Edge, and query result types
- No classes where a function suffices
- Keep extractors language-specific: one file per language, shared base interface
- Graph queries return plain dicts (JSON-serialisable for MCP responses)
- Tests use the fixture repos under tests/fixtures/

## Key Design Decisions

- GraphStore is an abstraction layer — methods like `get_callers()`, `impact_analysis()`, `find_hotspots()` hide the NetworkX implementation so we can swap to Memgraph later without changing MCP tools
- Node IDs are `"{file_path}::{name}::{line_start}"` for functions/classes, just `"{file_path}"` for files
- Import resolution happens in a separate pass after all files are parsed — the resolver needs the full list of extracted entities to match imports to definitions
- MCP tools return structured dicts with consistent shapes. Always include the target entity info, the results, and a count

## File Ignore List

When walking repos, always skip: `.git`, `node_modules`, `__pycache__`, `venv`, `.venv`, `dist`, `build`, `.next`, `coverage`, `.pytest_cache`, `.mypy_cache`, `target`, `.unlearn`, `.idea`, `.vscode`

## Testing

Test fixtures are real (small) codebases under `tests/fixtures/`. Each test file focuses on one component. Integration tests run the full pipeline: index fixture → build graph → run queries → verify results. When adding a new extractor or query, always add a test that uses the fixture repos.

## The Spec

The full build spec is in UNLEARN_V01_SPEC.md at the project root. Read it for detailed data models, MCP tool definitions, extractor specs, and the build order.
