# Unlearn v0.1 — Build Spec

## What We're Building

A CLI tool that indexes a code repository into an in-memory graph, then exposes that graph via an MCP server so Claude Code (or any MCP client) can answer structural questions about the codebase — impact analysis, dependency tracing, hotspot detection, dead code finding — that LLMs can't reliably do by reading files alone.

**Goal for v0.1:** Index a single local repo, serve MCP tools via stdio, and demonstrate that Claude Code with Unlearn gives genuinely better answers than Claude Code alone on structural queries.

## Tech Stack

| Component          | Choice                          | Why                                          |
|--------------------|---------------------------------|----------------------------------------------|
| Language           | Python 3.11+                    | Best tree-sitter bindings, FastMCP is solid  |
| AST parsing        | tree-sitter                     | Multi-language, fast, reliable               |
| Graph (local)      | NetworkX (in-memory)            | No Docker dependency, good enough for v0.1   |
| Graph (future)     | Memgraph                        | Upgrade path when scale demands it           |
| MCP server         | FastMCP                         | Python-native, supports stdio + HTTP         |
| Package manager    | uv                              | Fast, modern Python packaging                |
| CLI framework      | click                           | Simple, well-documented                      |
| Serialisation      | JSON (graph cache to disk)      | .unlearn/graph.json for persistence          |

**Not using Memgraph in v0.1** — NetworkX in-memory graph is sufficient for single repos up to ~50k files. No Docker dependency means zero friction for testing. The graph interface will be abstracted so swapping to Memgraph later is a backend change, not a rewrite.

---

## Project Structure

```
unlearn/
├── pyproject.toml
├── README.md
├── src/
│   └── unlearn/
│       ├── __init__.py
│       ├── cli.py                  # CLI entry point (click)
│       ├── indexer/
│       │   ├── __init__.py
│       │   ├── pipeline.py         # Main indexing orchestrator
│       │   ├── languages.py        # Language-specific tree-sitter configs
│       │   ├── extractors/
│       │   │   ├── __init__.py
│       │   │   ├── base.py         # Base extractor interface
│       │   │   ├── python.py       # Python AST extraction
│       │   │   ├── typescript.py   # TypeScript/JavaScript AST extraction
│       │   │   └── common.py       # Shared extraction utilities
│       │   └── resolver.py         # Import/call resolution across files
│       ├── graph/
│       │   ├── __init__.py
│       │   ├── store.py            # Graph interface (NetworkX backend)
│       │   ├── models.py           # Node and edge type definitions
│       │   ├── queries.py          # Pre-built graph queries
│       │   └── serialise.py        # JSON serialisation for disk cache
│       ├── mcp/
│       │   ├── __init__.py
│       │   └── server.py           # MCP server + tool definitions
│       └── utils/
│           ├── __init__.py
│           ├── files.py            # File system utilities
│           └── timing.py           # Performance timing helpers
├── tests/
│   ├── fixtures/                   # Small test repos
│   │   ├── python_simple/          # ~10 file Python project
│   │   └── typescript_simple/      # ~10 file TS project
│   ├── test_extractors.py
│   ├── test_graph.py
│   ├── test_queries.py
│   ├── test_mcp_tools.py
│   └── test_integration.py         # End-to-end: index → query
└── scripts/
    └── benchmark.py                # Compare unlearn vs claude code on test queries
```

---

## Core Components — Detailed Specs

### 1. CLI (`cli.py`)

```bash
# Index a repo (builds graph, caches to disk)
unlearn index [path]              # defaults to current directory
unlearn index --no-cache          # don't write .unlearn/graph.json
unlearn index --languages py,ts   # only parse specific languages

# Start MCP server (loads from cache or indexes first)
unlearn serve                     # stdio mode (for Claude Code)
unlearn serve --http              # HTTP mode (for remote clients)
unlearn serve --port 3000         # custom port for HTTP mode

# Info about the indexed graph
unlearn info [path]               # stats: node counts, edge counts, languages
```

**`unlearn index` flow:**
1. Walk the directory tree, skip `.git/`, `node_modules/`, `__pycache__/`, `venv/`, `.env/`, `dist/`, `build/`
2. Filter to supported file extensions (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`)
3. For each file: parse with tree-sitter, extract entities + relationships
4. After all files parsed: resolve cross-file imports and calls
5. Write graph to `.unlearn/graph.json`
6. Print summary: files indexed, nodes created, edges created, time taken

**`unlearn serve` flow:**
1. Check for `.unlearn/graph.json` — if exists, load it
2. If no cache, run index first
3. Start FastMCP server with stdio transport
4. Register all MCP tools
5. Wait for connections

### 2. Indexer

#### File Discovery (`pipeline.py`)

```python
DEFAULT_IGNORE = {
    ".git", "node_modules", "__pycache__", "venv", ".venv",
    "env", ".env", "dist", "build", ".next", ".nuxt",
    "coverage", ".pytest_cache", ".mypy_cache", "target",
    ".unlearn", ".idea", ".vscode"
}

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
}
```

Walk tree, collect file paths, group by language.

#### AST Extraction

For each file, tree-sitter produces an AST. We walk it and extract:

**Entities to Extract (Nodes):**

| Entity     | Extracted From                                  | Key Properties                                       |
|------------|------------------------------------------------|------------------------------------------------------|
| File       | Filesystem                                      | path, language, size_bytes                           |
| Function   | `function_declaration`, `function_definition`, `arrow_function`, `method_definition` | name, file_path, line_start, line_end, params (names + types if available), return_type, is_async, is_exported, is_method |
| Class      | `class_declaration`, `class_definition`         | name, file_path, line_start, line_end, decorators, bases (parent classes) |
| Type       | `type_alias_declaration`, `interface_declaration`, `enum` (TS); type annotations (Python) | name, file_path, kind (interface/type_alias/enum) |
| Import     | `import_statement`, `import_from_statement`     | source_path, imported_names, is_dynamic              |

**Relationships to Extract (Edges):**

| Edge           | Detection Method                                                        |
|----------------|-------------------------------------------------------------------------|
| FILE_CONTAINS  | Parent-child in AST: file → function/class/type                         |
| CALLS          | `call_expression` nodes where callee resolves to a known function       |
| IMPORTS        | Import statements → resolved file paths                                 |
| INHERITS       | Class base classes → resolved class nodes                               |
| REFERENCES     | Type annotations on params, return types, variable declarations         |

#### Python Extractor (`extractors/python.py`)

tree-sitter node types to match:

```python
FUNCTION_NODES = ["function_definition"]
CLASS_NODES = ["class_definition"]
IMPORT_NODES = ["import_statement", "import_from_statement"]
CALL_NODES = ["call"]
DECORATOR_NODES = ["decorator"]

# Extract function:
# - name: identifier child
# - params: parameters → [identifier children]
# - return_type: return_type child (if present)
# - is_async: parent is "async" or node text starts with "async"
# - decorators: preceding decorator nodes
# - line_start/end: start_point[0], end_point[0]

# Extract class:
# - name: identifier child
# - bases: argument_list child → [identifier children]
# - decorators: preceding decorator nodes

# Extract imports:
# import foo → imports "foo" (module)
# from foo import bar → imports "bar" from "foo"
# from foo.bar import baz → imports "baz" from "foo.bar"
# from . import foo → relative import
# from .foo import bar → relative import

# Resolve import paths:
# "from auth.middleware import validate" →
#   1. Look for auth/middleware.py in project
#   2. Find "validate" function/class in that file's extracted entities
#   3. Create IMPORTS edge: this_file → auth/middleware.py
#   4. If validate is a function we extracted, create CALLS edge too
```

#### TypeScript/JavaScript Extractor (`extractors/typescript.py`)

tree-sitter node types to match:

```python
FUNCTION_NODES = [
    "function_declaration",
    "method_definition",
    "arrow_function",          # const foo = () => {} 
]
CLASS_NODES = ["class_declaration"]
INTERFACE_NODES = ["interface_declaration"]
TYPE_ALIAS_NODES = ["type_alias_declaration"]
ENUM_NODES = ["enum_declaration"]
IMPORT_NODES = ["import_statement"]
EXPORT_NODES = ["export_statement"]
CALL_NODES = ["call_expression"]

# Arrow functions need special handling:
# const foo = () => {} → the name comes from the variable_declarator parent
# export const foo = () => {} → also exported

# Imports:
# import { foo } from './bar' → imports "foo" from "./bar"
# import foo from './bar' → default import
# import * as foo from './bar' → namespace import
# const foo = require('./bar') → CommonJS import

# Exports:
# export function foo() {} → is_exported = true
# export default function foo() {} → is_exported = true
# export { foo, bar } → mark foo, bar as exported
# module.exports = foo → CommonJS export
```

#### Import Resolution (`resolver.py`)

After all files are parsed, resolve import paths to actual files:

```python
def resolve_import(source_file: str, import_path: str, project_root: str) -> str | None:
    """
    Resolve an import path to an actual file in the project.
    
    Examples:
      resolve_import("src/auth/index.ts", "./middleware", "/project")
      → "src/auth/middleware.ts" (or .tsx, .js, /index.ts, etc.)
      
      resolve_import("src/routes/api.py", "auth.middleware", "/project")
      → "src/auth/middleware.py" (Python dotted path)
    """
    # TypeScript/JavaScript resolution order:
    # 1. Exact path: ./foo.ts
    # 2. Add extension: ./foo → ./foo.ts, ./foo.tsx, ./foo.js, ./foo.jsx
    # 3. Index file: ./foo → ./foo/index.ts, ./foo/index.js
    # 4. Package (node_modules) → mark as external, don't resolve
    
    # Python resolution:
    # 1. Dotted path to file: auth.middleware → auth/middleware.py
    # 2. Dotted path to package: auth → auth/__init__.py
    # 3. Relative: .middleware → ./middleware.py (relative to current file's dir)
    # 4. Stdlib/third-party → mark as external, don't resolve
```

#### Call Resolution

After imports are resolved, walk all `call_expression` nodes and try to resolve the callee:

```python
def resolve_call(call_node, file_imports: dict, file_entities: dict) -> str | None:
    """
    Given a call like `validateToken(req)`, figure out which function node it refers to.
    
    1. Check if callee name matches an import: validateToken was imported from ./auth
       → CALLS edge to that function
    2. Check if callee name matches a function in the same file
       → CALLS edge to that function  
    3. Check if callee is a method call: self.validate() or this.validate()
       → resolve via class hierarchy
    4. If unresolved, skip (don't create edge)
    """
```

### 3. Graph Store (`graph/store.py`)

Abstract interface over NetworkX. This is the swap point for Memgraph later.

```python
from dataclasses import dataclass
from enum import Enum
import networkx as nx

class NodeType(Enum):
    FILE = "File"
    FUNCTION = "Function"
    CLASS = "Class"
    TYPE = "Type"

class EdgeType(Enum):
    CONTAINS = "CONTAINS"       # File → Function/Class/Type
    CALLS = "CALLS"             # Function → Function
    IMPORTS = "IMPORTS"         # File → File
    INHERITS = "INHERITS"      # Class → Class
    REFERENCES = "REFERENCES"  # Function → Type

@dataclass
class Node:
    id: str           # unique: "{file_path}::{name}::{line_start}" or just file_path for File nodes
    type: NodeType
    name: str
    file_path: str
    properties: dict   # everything else: line_start, line_end, params, etc.

@dataclass
class Edge:
    source_id: str
    target_id: str
    type: EdgeType
    properties: dict   # call_site_line, import_path, etc.

class GraphStore:
    """NetworkX-backed graph store. Interface designed to be swappable to Memgraph."""
    
    def __init__(self):
        self._graph = nx.DiGraph()
    
    def add_node(self, node: Node) -> None: ...
    def add_edge(self, edge: Edge) -> None: ...
    def get_node(self, node_id: str) -> Node | None: ...
    
    # Query methods (these are what MCP tools call)
    def get_callers(self, node_id: str, depth: int = 1) -> list[Node]: ...
    def get_callees(self, node_id: str, depth: int = 1) -> list[Node]: ...
    def get_imports(self, file_path: str) -> list[Node]: ...
    def get_imported_by(self, file_path: str) -> list[Node]: ...
    def get_file_entities(self, file_path: str) -> list[Node]: ...
    
    # Traversal queries
    def trace_chain(self, from_id: str, direction: str, max_depth: int) -> list[dict]: ...
    def impact_analysis(self, node_id: str, max_depth: int) -> dict: ...
    def find_hotspots(self, top_n: int) -> list[dict]: ...
    def find_orphans(self) -> list[Node]: ...
    def find_cycles(self, max_length: int) -> list[list[str]]: ...
    
    # Search
    def search_by_name(self, query: str, node_types: list[NodeType] = None) -> list[Node]: ...
    
    # Stats
    def stats(self) -> dict: ...
    
    # Serialisation
    def to_json(self) -> dict: ...
    @classmethod
    def from_json(cls, data: dict) -> "GraphStore": ...
```

### 4. MCP Server (`mcp/server.py`)

Using FastMCP. These are the tools Claude Code will see and call.

**v0.1 ships with 6 tools.** These are the ones where the graph genuinely beats Claude Code reading files:

---

#### Tool: `impact_analysis`

**This is the flagship tool.** "What breaks if I change X?"

```python
@mcp.tool()
def impact_analysis(
    entity: str,         # function/class/type name
    change_type: str = "modify",  # "modify" | "delete" | "rename"  
    max_depth: int = 5
) -> dict:
    """
    Analyse the downstream impact of changing a code entity.
    Returns all directly and transitively affected functions, classes,
    and files — with depth information and risk assessment.
    
    Use this when: the user asks what would break/be affected if they
    change, delete, rename, or refactor something.
    """
    # 1. Find the target node(s) by name (may be multiple if name is ambiguous)
    # 2. Traverse all incoming CALLS, IMPORTS, REFERENCES, INHERITS edges
    # 3. For each affected node, record the depth and relationship chain
    # 4. Deduplicate and sort by depth
    # 5. Compute risk score based on: number affected, depth, presence of entry points
    
    return {
        "target": { "name": ..., "type": ..., "file_path": ..., "line": ... },
        "directly_affected": [
            { "name": ..., "type": ..., "file_path": ..., "relationship": "CALLS" }
        ],
        "transitively_affected": [
            { "name": ..., "type": ..., "file_path": ..., "depth": 2, "via": "..." }
        ],
        "affected_files": ["src/auth/middleware.ts", "src/routes/api.ts"],
        "total_affected": 17,
        "risk_score": "high",  # low (<5 affected), medium (5-15), high (>15)
        "risk_reason": "Widely imported utility function with 12 direct callers"
    }
```

---

#### Tool: `trace_dependencies`

"Show me the full path from A to B."

```python
@mcp.tool()
def trace_dependencies(
    entity: str,
    direction: str = "downstream",  # "upstream" | "downstream" | "both"
    max_depth: int = 8
) -> dict:
    """
    Trace the full dependency chain from a code entity — every function it calls
    (downstream) or every function that calls it (upstream), transitively.
    
    Use this when: the user asks about call chains, request flows, data flows,
    or wants to understand how deep a dependency goes.
    """
    return {
        "target": { "name": ..., "file_path": ... },
        "chain": [
            { "depth": 1, "name": "validateToken", "file": "auth/jwt.ts", "relationship": "CALLS" },
            { "depth": 2, "name": "verifySignature", "file": "auth/crypto.ts", "relationship": "CALLS" },
            { "depth": 3, "name": "getPublicKey", "file": "auth/keys.ts", "relationship": "CALLS" },
        ],
        "total_depth": 3,
        "affected_files": ["auth/jwt.ts", "auth/crypto.ts", "auth/keys.ts"]
    }
```

---

#### Tool: `find_hotspots`

"What are the most critical functions?"

```python
@mcp.tool()
def find_hotspots(top_n: int = 10) -> dict:
    """
    Find the most connected and most critical code entities in the codebase.
    Ranks by total connections (callers + callees + importers).
    
    Use this when: the user asks about critical code, high-risk functions,
    most important parts of the codebase, or where to focus testing.
    """
    return {
        "hotspots": [
            {
                "name": "validateToken",
                "type": "Function",
                "file_path": "src/auth/jwt.ts",
                "callers": 23,
                "callees": 4,
                "total_connections": 27,
                "risk": "Very high — single point of failure for auth"
            }
        ]
    }
```

---

#### Tool: `find_dead_code`

"What code is never called?"

```python
@mcp.tool()
def find_dead_code() -> dict:
    """
    Find exported functions and classes that have zero callers and are not
    entry points (not HTTP handlers, CLI commands, test functions, etc.).
    These are candidates for removal.
    
    Use this when: the user asks about dead code, unused functions, 
    cleanup opportunities, or code they can safely delete.
    """
    return {
        "dead_code": [
            { "name": "legacyParser", "type": "Function", "file_path": "src/utils/parse.ts", "line": 45 }
        ],
        "total_dead": 7,
        "note": "Excludes test functions, entry points, and lifecycle hooks"
    }
```

---

#### Tool: `find_circular_dependencies`

"Are there any circular imports?"

```python
@mcp.tool()
def find_circular_dependencies(max_cycle_length: int = 6) -> dict:
    """
    Detect circular dependency chains where module A imports B imports C imports A.
    Returns all cycles found up to the specified length.
    
    Use this when: the user asks about circular dependencies, import cycles,
    or architectural issues in the codebase.
    """
    return {
        "cycles": [
            { "chain": ["src/auth/index.ts", "src/users/service.ts", "src/auth/roles.ts", "src/auth/index.ts"], "length": 3 }
        ],
        "total_cycles": 2
    }
```

---

#### Tool: `get_context`

"Tell me about this function and everything connected to it."

```python
@mcp.tool()
def get_context(
    entity: str,       # function/class/file name or path
    depth: int = 1     # how many hops in the graph
) -> dict:
    """
    Get the full graph context for a code entity — what it is, what calls it,
    what it calls, what types it uses, and its siblings in the same file.
    
    Use this when: the user asks about a specific function, class, or file
    and you want complete structural context to give a thorough answer.
    """
    return {
        "target": {
            "name": ..., "type": ..., "file_path": ...,
            "line_start": ..., "line_end": ...,
            "params": [...], "return_type": ...
        },
        "callers": [...],
        "callees": [...],
        "imported_by": [...],
        "imports": [...],
        "types_referenced": [...],
        "siblings": [...]   # other functions/classes in the same file
    }
```

---

### 5. Graph Cache (`.unlearn/graph.json`)

Simple JSON serialisation of the full graph:

```json
{
    "version": "0.1",
    "indexed_at": "2026-04-01T12:00:00Z",
    "root": "/path/to/repo",
    "stats": {
        "files": 234,
        "functions": 891,
        "classes": 67,
        "types": 45,
        "edges": 2340,
        "index_time_ms": 8200
    },
    "nodes": [
        {
            "id": "src/auth/jwt.ts::validateToken::42",
            "type": "Function",
            "name": "validateToken",
            "file_path": "src/auth/jwt.ts",
            "properties": {
                "line_start": 42,
                "line_end": 68,
                "params": ["token: string", "options?: ValidateOptions"],
                "return_type": "Promise<TokenPayload>",
                "is_async": true,
                "is_exported": true
            }
        }
    ],
    "edges": [
        {
            "source": "src/routes/api.ts::handleRequest::15",
            "target": "src/auth/jwt.ts::validateToken::42",
            "type": "CALLS",
            "properties": { "call_site_line": 23 }
        }
    ]
}
```

---

## Integration with Claude Code

### .mcp.json (committed to repo)

Once `unlearn index` has run, the user adds this to their repo:

```json
{
    "mcpServers": {
        "unlearn": {
            "command": "unlearn",
            "args": ["serve"],
            "env": {}
        }
    }
}
```

Or for npx (no global install):

```json
{
    "mcpServers": {
        "unlearn": {
            "command": "uvx",
            "args": ["unlearn", "serve"],
            "env": {}
        }
    }
}
```

Claude Code auto-discovers this and launches the MCP server on startup.

---

## Testing Plan — Is It Actually Better?

### Test Fixture Repos

Create two test repos under `tests/fixtures/`:

**`python_simple/`** (~15 files, a Flask API):
```
python_simple/
├── app.py                    # Flask app, route definitions
├── auth/
│   ├── __init__.py
│   ├── jwt.py                # Token validation, generation
│   └── middleware.py          # Auth middleware (calls jwt.py)
├── models/
│   ├── __init__.py
│   ├── user.py               # User model
│   └── payment.py            # Payment model (imports user.py)
├── routes/
│   ├── __init__.py
│   ├── users.py              # User endpoints (imports auth, models)
│   └── payments.py           # Payment endpoints (imports auth, models)
├── services/
│   ├── __init__.py
│   ├── email.py              # Email service
│   └── stripe.py             # Stripe integration (imports models)
├── utils/
│   ├── __init__.py
│   ├── helpers.py            # Common utilities
│   └── deprecated.py         # Dead code — never imported by anything
└── tests/
    └── test_auth.py
```

**`typescript_simple/`** (~15 files, an Express API):
```
typescript_simple/
├── src/
│   ├── index.ts              # Express app entry point
│   ├── auth/
│   │   ├── jwt.ts            # Token validation
│   │   ├── middleware.ts      # Auth middleware
│   │   └── roles.ts          # Role-based access (circular dep with middleware)
│   ├── types/
│   │   ├── user.ts           # UserType interface
│   │   └── payment.ts        # PaymentType (imports UserType)
│   ├── routes/
│   │   ├── users.ts          # User endpoints
│   │   └── payments.ts       # Payment endpoints
│   ├── services/
│   │   ├── email.ts          # Email service
│   │   ├── stripe.ts         # Stripe (deep call chain)
│   │   └── legacy.ts         # Exported but never called
│   └── utils/
│       └── helpers.ts
└── package.json
```

These are designed to exercise the key scenarios: deep call chains, impact analysis across modules, circular dependencies, dead code.

### Benchmark Script (`scripts/benchmark.py`)

A set of queries to run against both Claude Code (plain) and Claude Code + Unlearn:

```python
BENCHMARK_QUERIES = [
    {
        "id": "impact_1",
        "category": "Impact Analysis",
        "query": "What would break if I deleted the validateToken function?",
        "expected": {
            "must_mention": ["middleware", "routes/users", "routes/payments"],
            "must_not_miss": ["authMiddleware"],  # key caller
            "transitive_depth": 2  # should find things 2+ hops away
        }
    },
    {
        "id": "trace_1",
        "category": "Dependency Tracing",
        "query": "Trace the full call chain from the POST /payments endpoint to the database/external API",
        "expected": {
            "chain_length": 4,  # route → service → stripe → (external)
            "must_include": ["handlePayment", "chargeStripe"]
        }
    },
    {
        "id": "hotspot_1",
        "category": "Hotspot Detection",
        "query": "What are the most critical functions in this codebase?",
        "expected": {
            "top_3_must_include": ["validateToken"],
            "must_provide_counts": True
        }
    },
    {
        "id": "dead_1",
        "category": "Dead Code",
        "query": "Find any dead or unused code in this project",
        "expected": {
            "must_find": ["deprecated.py functions", "legacy.ts exports"],
            "false_positives_ok": False  # shouldn't flag entry points as dead
        }
    },
    {
        "id": "circular_1",
        "category": "Circular Dependencies",
        "query": "Are there any circular dependency issues?",
        "expected": {
            "must_find_cycle": ["roles.ts", "middleware.ts"]
        }
    },
    {
        "id": "context_1",
        "category": "Entity Context",
        "query": "Tell me everything about the User model — what uses it, what it depends on",
        "expected": {
            "must_include_callers": True,
            "must_include_dependents": True,
            "must_include_type_references": True
        }
    }
]
```

### Evaluation Criteria

For each query, score on:

| Metric         | How to measure                                              |
|----------------|-------------------------------------------------------------|
| Completeness   | Did it find all expected entities? (count missed vs found)  |
| Correctness    | Were there false positives / hallucinated relationships?    |
| Depth           | Did it follow transitive chains or stop at 1 hop?          |
| Speed          | Wall clock time from query to complete answer               |
| Determinism    | Run 3 times — are answers consistent?                       |

### How to Run the Benchmark

```bash
# 1. Index the test repo
unlearn index tests/fixtures/python_simple

# 2. Start MCP server in background
unlearn serve &

# 3. Run same queries with Claude Code + Unlearn MCP
#    (manual for now — copy/paste queries into Claude Code session)
#    Record: answer quality, time, completeness

# 4. Run same queries with plain Claude Code (no Unlearn)
#    Record: answer quality, time, completeness

# 5. Compare
python scripts/benchmark.py --results-a with_unlearn.json --results-b without.json
```

For v0.1, the benchmark is manual — you run the queries in Claude Code and score the answers yourself. Automated evaluation is a v0.2 thing.

---

## What Success Looks Like

After v0.1, you should be able to:

1. **`unlearn index .`** on a Python or TypeScript repo and get a graph in <10 seconds for a medium repo (~200 files)

2. **`unlearn serve`** and have Claude Code call the MCP tools when you ask structural questions

3. **Demonstrate measurably better answers** on impact analysis, dependency tracing, hotspot detection, dead code finding, and circular dependency detection vs Claude Code alone

4. **Demonstrate faster answers** — graph queries return in milliseconds vs 30-60 seconds of Claude Code file reading for complex structural queries

The benchmark results should show Unlearn winning on at least 4 of the 6 benchmark queries in completeness and/or speed.

---

## Build Order

Build in this order — each step is testable independently:

### Step 1: Tree-sitter setup + Python extractor
- Install tree-sitter, tree-sitter-python
- Write the Python extractor: extract functions, classes, imports
- Test: parse `tests/fixtures/python_simple/`, verify correct entity extraction
- **Checkpoint: `pytest tests/test_extractors.py` passes**

### Step 2: Graph store + edge resolution
- Implement GraphStore with NetworkX
- Implement import resolver for Python
- Implement call resolver
- Build graph from extracted entities + resolved edges
- Test: graph for python_simple has expected nodes and edges
- **Checkpoint: `pytest tests/test_graph.py` passes**

### Step 3: Graph queries
- Implement: impact_analysis, trace_chain, find_hotspots, find_orphans, find_cycles, get_context
- Test: each query returns expected results on python_simple
- **Checkpoint: `pytest tests/test_queries.py` passes**

### Step 4: MCP server
- Implement FastMCP server with all 6 tools
- Wire tools to graph queries
- Test: MCP tools return correct JSON
- **Checkpoint: `pytest tests/test_mcp_tools.py` passes**

### Step 5: CLI + cache
- Implement `unlearn index`, `unlearn serve`, `unlearn info`
- Implement JSON serialisation/deserialisation
- Test: index → cache → load → query gives same results
- **Checkpoint: `pytest tests/test_integration.py` passes**

### Step 6: TypeScript extractor
- Write TS extractor: functions (including arrow functions), classes, interfaces, types, imports, exports
- Implement TS import resolver
- Test on typescript_simple fixture
- **Checkpoint: full test suite passes for both Python + TS**

### Step 7: Benchmark
- Create benchmark script
- Run queries manually in Claude Code with and without Unlearn
- Document results
- **Checkpoint: results show improvement on 4+ of 6 queries**

---

## Dependencies

```toml
# pyproject.toml
[project]
name = "unlearn"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "tree-sitter>=0.23",
    "tree-sitter-python>=0.23",
    "tree-sitter-javascript>=0.23",
    "tree-sitter-typescript>=0.23",
    "networkx>=3.2",
    "fastmcp>=0.1",
    "click>=8.1",
]

[project.scripts]
unlearn = "unlearn.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.23"]
```

---

## Constraints / Decisions

1. **No Docker in v0.1.** NetworkX in-memory. Memgraph comes later.
2. **No embeddings in v0.1.** Search is name-based substring matching. Semantic search comes later.
3. **No LLM enrichment in v0.1.** No docstring generation. Pure structural extraction.
4. **No HTTP transport in v0.1.** Stdio only (sufficient for Claude Code). HTTP comes in v0.2.
5. **Python + TypeScript/JavaScript only.** Go, Rust, Java come later.
6. **Single repo only.** Cross-repo comes later.
7. **No incremental indexing in v0.1.** Full re-index every time. Incremental comes later.
8. **No authentication.** Local only, no auth needed.
