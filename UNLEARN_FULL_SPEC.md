# Unlearn — Codebase Knowledge Infrastructure for AI Agents

## Project Summary

Unlearn is a codebase knowledge infrastructure platform that parses code repositories into a rich knowledge graph (Memgraph), then exposes that graph to any LLM or AI agent via an MCP (Model Context Protocol) server. Unlike monolithic solutions like Potpie that own the full agent stack, Unlearn is **infrastructure** — it provides the structured context layer, and lets any MCP-compatible client (Claude Code, Cursor, custom agents) consume it.

**One-liner:** "The knowledge brain your AI agents plug into."

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          UNLEARN                                    │
│                                                                     │
│  ┌──────────┐     ┌──────────────┐     ┌───────────────────────┐   │
│  │ GitHub   │────▶│  Indexing     │────▶│     Memgraph          │   │
│  │ App      │     │  Pipeline     │     │  (Knowledge Graph)    │   │
│  │ (Webhook │     │              │     │                       │   │
│  │  + Clone)│     │  - tree-sitter│     │  Org-level graph:     │   │
│  └──────────┘     │  - AST walk   │     │  repo A ──▶ repo B    │   │
│       │           │  - Embedding  │     │  repo B ──▶ repo C    │   │
│       │           │    generation │     │  shared resources     │   │
│       │           └──────┬───────┘     └───────────┬───────────┘   │
│       │                  │                         │               │
│       │                  │         ┌───────────────┼────────────┐  │
│       │                  │         │               │            │  │
│       │                  ▼         ▼               ▼            │  │
│       │           ┌─────────┐  ┌─────────┐  ┌──────────────┐   │  │
│       │           │ MODE 1  │  │ MODE 2  │  │   MODE 3     │   │  │
│       │           │ Static  │  │ Local   │  │   Cloud      │   │  │
│       │           │         │  │ Graph   │  │   Graph      │   │  │
│       │           │CODEBASE │  │ MCP via │  │   MCP via    │   │  │
│       │           │  .md    │  │ stdio   │  │   HTTP       │   │  │
│       └──────────▶│         │  │         │  │              │   │  │
│   (also works     │ORG_GRAPH│  │ All MCP │  │ All MCP      │   │  │
│    without        │  .md    │  │ tools   │  │ tools +      │   │  │
│    GitHub App)    │         │  │         │  │ cross-repo   │   │  │
│                   └────┬────┘  └────┬────┘  └──────┬───────┘   │  │
│                        │            │              │            │  │
└────────────────────────┼────────────┼──────────────┼────────────┘  │
                         │            │              │               │
              ┌──────────▼──┐  ┌──────▼─────┐  ┌────▼──────────┐   │
              │ Any LLM tool│  │ Claude Code │  │ Claude Code   │   │
              │ (reads .md) │  │ Cursor      │  │ Cursor        │   │
              │ ChatGPT     │  │ (local)     │  │ Custom Agents │   │
              │ Cursor      │  │             │  │ (remote)      │   │
              └─────────────┘  └─────────────┘  └───────────────┘   │
```

---

## Core Components

### 1. GitHub App (Ingestion Layer)

**Purpose:** Repository access, webhook-driven incremental updates.

**Implementation:**
- Distributed as a GitHub App (installable via GitHub Marketplace)
- On install: receives `installation` webhook, queues full repo parse
- On push/PR: receives `push` / `pull_request` webhooks, queues incremental update
- Clones repos to temp storage using installation access tokens
- Supports GitHub.com initially; GitLab / self-hosted Git as follow-up

**Webhook Events to Subscribe:**
- `installation` — new repo connected
- `installation_repositories` — repos added/removed
- `push` — commits to default branch (triggers incremental re-index)
- `pull_request` — PR opened/updated (triggers diff-aware context)
- `repository` — repo renamed/deleted (triggers graph cleanup)

**Auth Flow:**
- GitHub App generates short-lived installation tokens per repo
- Tokens stored in-memory only, never persisted
- User authenticates to Unlearn via GitHub OAuth (for dashboard/management)

**Tech:**
- Webhook receiver: FastAPI endpoint
- Queue: Redis + Celery (or BullMQ if going Node)
- Temp clone storage: ephemeral filesystem, cleaned after parse

---

### 2. Indexing Pipeline (Parser)

**Purpose:** Parse repository source code into a structured knowledge graph.

**Strategy:** AST-first, LLM-optional enrichment.

#### Stage 1: Structural Extraction (No LLM Required)

Uses **tree-sitter** for multi-language AST parsing.

**Supported languages (launch):**
- Python
- TypeScript / JavaScript
- Go
- Rust
- Java

**Extraction targets:**

| Entity (Node)  | Properties                                                     |
|-----------------|----------------------------------------------------------------|
| `Repository`    | name, url, default_branch, language_breakdown                  |
| `File`          | path, language, size_bytes, last_modified                      |
| `Module`        | name, file_path, export_type (default/named)                   |
| `Class`         | name, file_path, line_start, line_end, decorators              |
| `Function`      | name, file_path, line_start, line_end, params, return_type, is_async, is_exported |
| `Type`          | name, file_path, kind (interface/type_alias/enum/struct)       |
| `Endpoint`      | method, path, handler_function (inferred from framework patterns) |
| `Package`       | name, version (from package.json / pyproject.toml / go.mod)    |

**Relationships (Edges):**

| Relationship     | From         | To           | Properties                |
|------------------|--------------|--------------|---------------------------|
| `CONTAINS`       | File         | Class/Function/Type | —                    |
| `CALLS`          | Function     | Function     | call_site_line            |
| `IMPORTS`        | File/Module  | File/Module  | import_path, is_dynamic   |
| `INHERITS`       | Class        | Class        | —                         |
| `IMPLEMENTS`     | Class        | Type         | —                         |
| `DEPENDS_ON`     | Package      | Package      | version_constraint        |
| `DEFINES`        | File         | Endpoint     | framework                 |
| `EXPORTS`        | Module       | Function/Class/Type | export_name          |
| `REFERENCES`     | Function     | Type         | usage_kind (param/return/variable) |
| `BELONGS_TO`     | File         | Repository   | —                         |

#### Stage 2: Semantic Enrichment (LLM, Optional/Async)

After structural extraction, optionally enrich nodes with:
- **Docstring summaries** — LLM-generated one-liner for each function/class describing what it does in context of its callers/callees
- **Module purpose inference** — "This module handles authentication middleware"
- **Endpoint documentation** — inferred request/response shapes

This runs async and is **not blocking** — the graph is queryable immediately after Stage 1. Enrichment adds value but isn't required for core functionality.

**LLM usage for enrichment:**
- Model: configurable (default: Claude Haiku for cost efficiency)
- User provides their own API key, OR Unlearn provides a managed tier
- Rate limited, batched, with caching (don't re-enrich unchanged nodes)

#### Stage 3: Embedding Generation

For each node, generate a vector embedding of:
- Node name + docstring + file path + relationship context
- Stored as a property on the node in Memgraph (or in a sidecar vector index)

**Embedding model:** Configurable. Default: `text-embedding-3-small` (OpenAI) or Voyage Code.

**Purpose:** Powers semantic search tool in the MCP server — "find functions related to payment processing"

#### Incremental Updates

This is a key differentiator. On `push` webhook:

1. Compute file diff from the commit(s)
2. For changed files only:
   - Re-parse AST with tree-sitter
   - Diff extracted entities against existing graph nodes
   - Update/add/remove nodes and edges as needed
   - Re-generate embeddings for changed nodes
   - Optionally re-run LLM enrichment for changed nodes
3. For deleted files: cascade-remove all child nodes and dangling edges

**Goal:** Incremental update completes in seconds for typical commits, not minutes.

---

### 3. Memgraph (Knowledge Graph Storage)

**Why Memgraph over Neo4j:**
- In-memory graph DB — significantly faster traversals for real-time MCP queries
- Cypher-compatible (easy migration path, familiar query language)
- Lower operational overhead than Neo4j for this scale
- Better suited for latency-sensitive tool calls (MCP tools need to respond fast)

**Deployment:**
- Managed Memgraph Cloud for SaaS offering
- Self-hostable via Docker for on-prem / privacy-sensitive users
- Each user/org gets an isolated database (multi-tenant via Memgraph database namespacing)

**Indexes:**
- Node label indexes on all entity types
- Property indexes on: `name`, `file_path`, `repository_id`
- Full-text index on node names + docstrings (for search tool)
- Vector index for embedding-based similarity search (if Memgraph supports it natively; otherwise sidecar with pgvector or Qdrant)

**Schema constraints:**
- Unique constraint on `(Repository.url)`
- Unique constraint on `(File.path, File.repository_id)`
- Unique constraint on `(Function.name, Function.file_path, Function.line_start)`

---

### 4. MCP Server (Query Layer)

**Purpose:** Expose the knowledge graph to any MCP-compatible client.

**Transport:** Streamable HTTP (the modern MCP transport — works with Claude Code, remote clients, deployed servers). Also support stdio for local dev.

**Auth:** Bearer token per user. Token issued on GitHub OAuth login, scoped to their installed repos.

**Framework:** Python FastMCP (or TypeScript MCP SDK — TBD based on preference).

#### MCP Tools

These are the tools that LLM clients will see and call:

---

**`list_repos`**
List all repositories the user has connected to Unlearn.

```
Input: {}
Output: [{ name, url, last_indexed, node_count, language_breakdown }]
```

---

**`get_architecture`**
Get a high-level architectural overview of a repository.

```
Input: { repo: string }
Output: {
  modules: [{ name, purpose, file_count, key_exports }],
  entry_points: [{ type, path, handler }],
  external_dependencies: [{ name, version }],
  language_breakdown: { ... },
  summary: string  // LLM-generated if enrichment is enabled
}
```

Use case: "Explain the architecture of this repo." New developer onboarding.

---

**`get_context`**
Get full context for a specific code entity — the entity itself plus its immediate graph neighbourhood.

```
Input: {
  repo: string,
  entity: string,       // function/class/file name or path
  depth: number = 1,    // how many hops in the graph to traverse
  include_code: boolean = false  // include raw source code of nodes
}
Output: {
  target: { type, name, file_path, line_range, docstring, code? },
  callers: [{ ... }],
  callees: [{ ... }],
  imports: [{ ... }],
  inherited_by: [{ ... }],
  inherits_from: [{ ... }],
  sibling_functions: [{ ... }],  // other functions in same file/class
  related_types: [{ ... }]
}
```

Use case: "What does `processPayment` do and what calls it?"

---

**`search_code`**
Semantic search across the codebase knowledge graph.

```
Input: {
  repo: string,
  query: string,         // natural language: "authentication middleware"
  entity_types: string[] = [],  // filter: ["Function", "Class", "Endpoint"]
  limit: number = 10
}
Output: [{
  type, name, file_path, line_range, docstring,
  relevance_score: float
}]
```

Use case: "Find all functions related to rate limiting."

---

**`trace_dependencies`**
Trace the full dependency chain from one entity — transitive calls, imports, type references.

```
Input: {
  repo: string,
  entity: string,
  direction: "upstream" | "downstream" | "both",
  max_depth: number = 5,
  include_external: boolean = false
}
Output: {
  chain: [{
    entity: { type, name, file_path },
    relationship: string,
    depth: number
  }],
  affected_files: string[],
  external_dependencies: string[]
}
```

Use case: "What's the full call chain from this API endpoint to the database?"

---

**`impact_analysis`**
Given a file or entity, determine what would be affected if it changed.

```
Input: {
  repo: string,
  entity: string,       // or file_path
  change_type: "modify" | "delete" | "rename"
}
Output: {
  directly_affected: [{ type, name, file_path, relationship }],
  transitively_affected: [{ type, name, file_path, depth }],
  affected_endpoints: [{ method, path }],
  affected_tests: [{ file_path, test_name }],
  risk_score: "low" | "medium" | "high",
  summary: string
}
```

Use case: "What breaks if I change this interface?" Blast radius analysis.

---

**`explain_module`**
Deep explanation of a module/directory — what it does, how it fits into the system, key entry points.

```
Input: {
  repo: string,
  path: string   // directory or module path
}
Output: {
  purpose: string,
  key_exports: [{ name, type, docstring }],
  internal_structure: string,    // description of how files in the module relate
  depends_on: [{ module, relationship }],
  depended_on_by: [{ module, relationship }],
  entry_points: [{ type, name, description }]
}
```

Use case: "What does the `auth/` directory do?"

---

**`query_graph`**
Raw Cypher query escape hatch for power users / advanced agents.

```
Input: {
  repo: string,
  cypher: string,      // raw Cypher query
  params: object = {}  // query parameters
}
Output: {
  rows: any[],
  columns: string[],
  execution_time_ms: number
}
```

Use case: Advanced structural queries that don't fit the pre-built tools. Should be used sparingly by agents.

**Security:** Queries are scoped to the user's repos via enforced `WHERE` clause injection. Read-only — no `CREATE`, `DELETE`, `SET`, `MERGE` allowed.

---

**`diff_context`**
Given a PR or commit diff, return the knowledge graph context for all changed entities.

```
Input: {
  repo: string,
  ref: string,          // PR number, commit SHA, or branch name
  include_affected: boolean = true
}
Output: {
  changed_entities: [{
    entity: { type, name, file_path },
    change_type: "added" | "modified" | "deleted",
    context: { callers, callees, related_types }  // same shape as get_context
  }],
  affected_entities: [{    // if include_affected=true
    entity: { type, name, file_path },
    affected_via: string,  // relationship chain
    depth: number
  }]
}
```

Use case: PR review — "what's the blast radius of this diff?"

---

### 5. MCP Resources (Passive Context)

In addition to tools (which agents call on-demand), MCP also supports **resources** — static context the client can pull in.

**`unlearn://repo/{repo}/architecture`** — always-current architecture summary
**`unlearn://repo/{repo}/module/{path}`** — module overview
**`unlearn://repo/{repo}/stats`** — repo statistics (node counts, language breakdown, last indexed)

These are useful for clients that want to pre-load context into the system prompt.

---

## Tech Stack

| Component              | Technology                              |
|------------------------|-----------------------------------------|
| MCP Server             | Python (FastMCP) or TypeScript (MCP SDK)|
| API / Webhooks         | FastAPI (Python) or Hono (TypeScript)   |
| Graph Database         | Memgraph (Cypher-compatible, in-memory) |
| AST Parsing            | tree-sitter (multi-language)            |
| Task Queue             | Redis + Celery (Python) or BullMQ (TS)  |
| Vector Embeddings      | OpenAI text-embedding-3-small / Voyage Code |
| Vector Storage         | Memgraph native (if supported) or Qdrant sidecar |
| Auth                   | GitHub OAuth + JWT tokens               |
| Hosting                | Railway / Fly.io / AWS (MCP server)     |
| Graph Hosting          | Memgraph Cloud or self-hosted Docker    |
| CI/CD                  | GitHub Actions                          |
| Monitoring             | Sentry + basic Prometheus metrics       |

---

## Distribution Model

### GitHub App (Primary)

1. User installs "Unlearn" GitHub App on their org/repos
2. Unlearn receives webhook, indexes the repo(s)
3. User gets an MCP server URL + auth token
4. User adds the MCP server to Claude Code / Cursor / etc:

```json
// Claude Code: ~/.claude/mcp_servers.json
{
  "unlearn": {
    "type": "url",
    "url": "https://mcp.unlearn.dev/sse",
    "headers": {
      "Authorization": "Bearer <token>"
    }
  }
}
```

```bash
# Or via CLI
claude mcp add unlearn --transport sse --url https://mcp.unlearn.dev/sse --header "Authorization: Bearer <token>"
```

### Self-Hosted (Secondary)

For teams that can't send code to external services:

```bash
docker compose up -d  # Starts Memgraph + Unlearn server + Redis

# Point at local repos
unlearn index ./my-repo
unlearn serve --port 3000

# Connect Claude Code to local server
claude mcp add unlearn --transport stdio --command "unlearn mcp"
```

---

## Output Modes

Unlearn operates in three modes, from zero-infrastructure to full graph. This is the adoption funnel — people enter at the lightweight end and upgrade as they hit limits.

### Mode 1: Static Knowledge File (`unlearn generate`)

**No Docker. No server. No account. Just a file.**

Unlearn ships a CLI that can parse a repo locally and output a `CODEBASE.md` (or `.unlearn/knowledge.json`) file that lives in the repo root. This file is readable by any LLM — Claude Code picks it up automatically as project context, Cursor reads it, even raw ChatGPT can consume it if pasted in.

```bash
# Install
npm install -g unlearn  # or pip install unlearn-cli

# Generate knowledge file for current repo
unlearn generate

# Output: ./CODEBASE.md  (also .unlearn/knowledge.json for structured access)
```

**What goes in CODEBASE.md:**

```markdown
# Codebase Knowledge — myapp

> Auto-generated by [Unlearn](https://unlearn.dev). Last updated: 2026-03-30

## Architecture Overview

This is a Node.js/TypeScript monorepo with 3 packages:
- `packages/api` — Express REST API (47 endpoints)
- `packages/web` — Next.js frontend
- `packages/shared` — Shared types and utilities

## Module Map

### packages/api/src/auth/
**Purpose:** Authentication and authorization middleware.
**Key exports:** `validateToken`, `requireRole`, `refreshSession`
**Depends on:** `packages/shared/types`, `jsonwebtoken`, `redis`
**Depended on by:** Every route handler in `packages/api/src/routes/`

### packages/api/src/routes/
**Purpose:** API route definitions. 47 endpoints across 8 route files.
**Key exports:** `apiRouter` (mounted at `/api/v1`)
**Depends on:** `auth/`, `services/`, `middleware/`
**Entry points:**
- POST /api/v1/payments/charge → `payments.ts:handleCharge`
- GET  /api/v1/users/:id        → `users.ts:getUser`
- ...

### packages/web/src/hooks/
**Purpose:** Custom React hooks for data fetching and state.
**Key exports:** `useAuth`, `usePayments`, `useQuery`
**Depends on:** `packages/shared/types`, `@tanstack/react-query`

[... continues for all significant modules ...]

## Dependency Graph (Key Relationships)

- `validateToken` is called by 23 functions across 8 files
- `packages/web` consumes 12 endpoints from `packages/api`
- `UserType` (shared/types) is referenced by 34 functions
- Critical path: Request → authMiddleware → validateToken → redis.get → routeHandler

## External Dependencies (Notable)

- express@4.18.2 — API framework
- next@14.1.0 — Frontend framework
- jsonwebtoken@9.0.0 — Token validation (used in auth/)
- redis@4.6.0 — Session store + cache

## Entry Points

| Type     | Path/Command               | Handler                    |
|----------|----------------------------|----------------------------|
| HTTP     | POST /api/v1/payments      | payments.ts:handleCharge   |
| HTTP     | GET /api/v1/users/:id      | users.ts:getUser           |
| Cron     | daily-cleanup              | jobs/cleanup.ts:run        |
| CLI      | `npm run migrate`          | scripts/migrate.ts:main    |
```

**What goes in `.unlearn/knowledge.json`:**

The same information but structured — nodes, edges, module summaries, dependency chains. This is for tools that want to parse it programmatically rather than feed it to an LLM as text.

```json
{
  "version": "0.1",
  "repo": "myapp",
  "generated_at": "2026-03-30T12:00:00Z",
  "stats": { "files": 234, "functions": 891, "classes": 67, "endpoints": 47 },
  "modules": [
    {
      "path": "packages/api/src/auth",
      "purpose": "Authentication and authorization middleware",
      "key_exports": ["validateToken", "requireRole", "refreshSession"],
      "depends_on": ["packages/shared/types", "jsonwebtoken", "redis"],
      "depended_on_by": ["packages/api/src/routes"]
    }
  ],
  "critical_paths": [],
  "entry_points": [],
  "dependency_graph": { "nodes": [], "edges": [] }
}
```

**Key design decisions for static mode:**

- **Runs entirely locally** — no API keys, no network calls, no account needed. Just tree-sitter parsing.
- **No LLM enrichment** in static mode — the summaries are template-generated from the graph structure, not LLM-written. This keeps it free and fast.
- **Regenerate on demand** — user runs `unlearn generate` whenever they want, or hooks it into a pre-commit / CI step.
- **File size budget** — CODEBASE.md targets < 50KB for most repos (fits comfortably in any LLM context window). For large repos, it prioritises the most-connected / most-imported modules and truncates the rest with a "run `unlearn generate --full` for complete output" note.
- **Claude Code auto-detection** — if CODEBASE.md exists in the project root, Claude Code will read it as project context automatically (same as CLAUDE.md). No configuration needed.
- **.gitignore friendly** — `.unlearn/` directory can be gitignored if the team doesn't want it committed. CODEBASE.md can be committed as living documentation.

**This is the free tier. This is how people discover Unlearn.**

### Mode 2: Local Graph (`unlearn serve`)

For users who want the full graph query power but don't want to use the cloud:

```bash
# Parse + load into local Memgraph + start MCP server
unlearn serve --repo ./my-repo

# Memgraph runs in an embedded/sidecar Docker container
# MCP server available at stdio (for Claude Code) or localhost:3000
```

This gives access to all MCP tools (impact_analysis, trace_dependencies, etc.) but runs entirely on the developer's machine. The graph lives in memory and is rebuilt on each `serve` invocation (or persisted to disk with `--persist`).

### Mode 3: Cloud Graph (`unlearn.dev`)

The full hosted product — GitHub App install, webhook-driven updates, managed Memgraph, remote MCP server. This is the paid tier.

```
Mode 1 (Static)  →  Mode 2 (Local Graph)  →  Mode 3 (Cloud Graph)
Free, no infra       Free, needs Docker       Paid, fully managed
CODEBASE.md          Local MCP server         Remote MCP server
Any LLM tool         Claude Code / Cursor     Claude Code / Cursor
Single repo          Single repo              Multi-repo + cross-repo
Point-in-time        Session-lived            Always current
```

---

## Cross-Repo Knowledge Graph

This is where the graph model genuinely differentiates from flat files or per-repo tools. As more repos are indexed under the same org, Unlearn builds an **organisation-level knowledge graph** that captures how repositories relate to each other.

### How Cross-Repo Edges Are Detected

**1. Package dependency resolution**

When repo A's `package.json` depends on `@myorg/shared-types@^2.0.0`, and repo B is `@myorg/shared-types`, Unlearn creates:

```cypher
(repoA:Repository)-[:DEPENDS_ON_REPO {via_package: "@myorg/shared-types", version: "^2.0.0"}]->(repoB:Repository)
```

And at the entity level:
```cypher
(functionInA:Function)-[:IMPORTS_FROM_REPO]->(typeInB:Type)
```

Detection: Parse `package.json` / `pyproject.toml` / `go.mod` across all indexed repos and match internal package names.

**2. API contract matching**

When repo A (frontend) makes HTTP calls to `POST /api/v1/payments/charge`, and repo B (backend) defines that endpoint:

```cypher
(callerInA:Function)-[:CALLS_ENDPOINT]->(endpointInB:Endpoint {method: "POST", path: "/api/v1/payments/charge"})
```

Detection:
- In repo B: extract endpoint definitions from framework patterns (Express routes, FastAPI decorators, etc.)
- In repo A: detect HTTP client calls (`fetch`, `axios`, generated API clients) and extract the URL patterns
- Match them. This is fuzzy — URL patterns might be templated, base URLs might be env vars — but high-confidence matches are valuable even if coverage isn't 100%.

**3. Shared type / schema references**

When both repos reference the same Protobuf schemas, OpenAPI specs, or GraphQL types:

```cypher
(repoA:Repository)-[:SHARES_SCHEMA {schema: "user.proto"}]->(repoB:Repository)
```

Detection: Look for shared schema files (`.proto`, `openapi.yaml`, `.graphql`) across repos, or detect generated client code that references external schemas.

**4. Infrastructure references**

When repo A's code references the same database tables, queue names, or S3 buckets as repo B:

```cypher
(functionInA:Function)-[:READS_FROM {resource: "users_table"}]->(functionInB:Function)-[:WRITES_TO {resource: "users_table"}]
```

Detection: String-match database table names, queue names, bucket names from code. Lower confidence but still useful.

### The Organisation Graph

As repos accumulate, the graph naturally forms an org-level topology:

```
                    ┌──────────────┐
                    │  shared-types │
                    │  (repo)       │
                    └──────┬───────┘
                     ▲     │     ▲
          IMPORTS    │     │     │   IMPORTS
                     │     │     │
              ┌──────┘     │     └──────┐
              │            │            │
     ┌────────▼──┐   ┌────▼─────┐   ┌──▼─────────┐
     │  frontend  │   │  backend  │   │  worker     │
     │  (repo)    │──▶│  (repo)   │   │  (repo)     │
     └───────────┘   └────┬─────┘   └──────┬──────┘
       CALLS_ENDPOINT     │                │
                          │  WRITES_TO     │ READS_FROM
                          ▼                ▼
                    ┌──────────────┐
                    │  payments_db  │
                    │  (resource)   │
                    └──────────────┘
```

### Cross-Repo MCP Tools

The existing tools naturally extend to cross-repo queries:

**`trace_dependencies`** with `include_cross_repo: true`:
```
Input:  trace_dependencies(entity="handlePayment", direction="downstream", include_cross_repo=true)
Output: handlePayment (backend) → calls chargeStripe (backend) → writes to payments_db
        → payments_db is read by generateInvoice (worker repo)
        → generateInvoice calls sendEmail (worker repo)
```

**`impact_analysis`** with cross-repo awareness:
```
Input:  impact_analysis(entity="UserType", repo="shared-types")
Output: {
  directly_affected_repos: ["frontend", "backend", "worker"],
  affected_entities: [
    { repo: "frontend", entity: "useUser hook", depth: 1 },
    { repo: "backend", entity: "getUserEndpoint", depth: 1 },
    { repo: "worker", entity: "processUserJob", depth: 2 }
  ],
  risk_score: "high"  // shared type = wide blast radius
}
```

**New tool — `get_org_topology`:**
```
Input:  {}
Output: {
  repos: [{ name, role, key_exports, depends_on_repos }],
  shared_resources: [{ type, name, accessed_by_repos }],
  api_contracts: [{ endpoint, provider_repo, consumer_repos }],
  critical_paths: [{ description, repos_involved, risk }]
}
```

### Cross-Repo in Static Mode

Even in CODEBASE.md mode, if a user runs `unlearn generate` across multiple repos, the CLI can detect cross-repo relationships from the local filesystem:

```bash
# Generate knowledge files for all repos in a workspace
unlearn generate --workspace ~/code/myorg/

# Each repo gets its own CODEBASE.md, PLUS:
# ~/code/myorg/.unlearn/ORG_GRAPH.md — the cross-repo topology
```

**ORG_GRAPH.md** would contain:
```markdown
# Organisation Knowledge Graph — myorg

## Repository Topology

- **frontend** (Next.js) → consumes 12 endpoints from **backend**
- **backend** (Express) → depends on **shared-types**, writes to payments_db
- **worker** (Node.js) → depends on **shared-types**, reads from payments_db
- **shared-types** (TypeScript) → consumed by frontend, backend, worker

## Cross-Repo Critical Paths

1. User signup: frontend → POST /api/v1/users (backend) → writes users_table
   → worker picks up welcome-email job
2. Payment flow: frontend → POST /api/v1/payments (backend) → Stripe API
   → writes payments_table → worker generates invoice

## Shared Resources

| Resource       | Type     | Writers          | Readers              |
|----------------|----------|------------------|----------------------|
| users_table    | Database | backend          | backend, worker      |
| payments_table | Database | backend          | worker               |
| email-queue    | Queue    | backend, worker  | worker               |
```

### Cross-Repo Confidence Levels

Not all cross-repo edges are equally reliable. Each edge gets a confidence score:

| Detection Method           | Confidence | Example                                     |
|----------------------------|------------|---------------------------------------------|
| Package dependency match   | High       | package.json → internal package              |
| Explicit API client import | High       | Generated client from OpenAPI spec            |
| URL pattern matching       | Medium     | `fetch("/api/v1/users")` → endpoint def      |
| Shared schema files        | Medium     | Both repos have `user.proto`                  |
| String-matched resources   | Low        | Same table name in SQL strings                |
| Inferred from naming       | Low        | Function names suggest cross-service call     |

Low-confidence edges are stored but flagged, and MCP tools can filter by confidence threshold.

---

## User Journey

### Setup — Static Mode (< 1 minute)

1. `npx unlearn generate` in your repo
2. CODEBASE.md appears in the project root
3. Open Claude Code / Cursor — it reads CODEBASE.md automatically
4. Done. Your AI tool now understands your codebase architecture.

### Setup — Cloud Mode (< 5 minutes)

1. Go to `unlearn.dev`, click "Install GitHub App"
2. Select repos to connect
3. Wait for initial indexing (progress shown on dashboard)
4. Copy MCP server URL + token
5. Paste into Claude Code / Cursor config
6. Done. Start asking structural questions about your code.

### Daily Use

The user never interacts with Unlearn directly. They just use their normal AI coding tools, and those tools have access to deep codebase knowledge via the MCP tools.

Example Claude Code session:
```
> "What would break if I removed the `validateToken` function?"

Claude Code calls: impact_analysis(repo="myapp", entity="validateToken", change_type="delete")

Claude: "Removing validateToken would affect 12 functions across 4 files.
The most critical impact is on the auth middleware pipeline —
authMiddleware.ts calls it on every request. Three API endpoints
in routes/api.ts would lose authentication. There are also 5 test
files that directly test this function..."
```

---

## Data Model (Memgraph Schema)

```cypher
// Node labels
CREATE CONSTRAINT ON (r:Repository) ASSERT r.url IS UNIQUE;
CREATE CONSTRAINT ON (f:File) ASSERT (f.path, f.repo_id) IS UNIQUE;

// Core entity nodes
(:Repository {url, name, default_branch, last_indexed_at, language_breakdown})
(:File {path, repo_id, language, size_bytes, hash})
(:Module {name, file_path, repo_id, export_type})
(:Class {name, file_path, repo_id, line_start, line_end, decorators, docstring, embedding})
(:Function {name, file_path, repo_id, line_start, line_end, params, return_type, is_async, is_exported, docstring, embedding})
(:Type {name, file_path, repo_id, kind, docstring, embedding})
(:Endpoint {method, path, repo_id, framework, handler_function})
(:Package {name, version, repo_id})

// Relationships
(File)-[:BELONGS_TO]->(Repository)
(File)-[:CONTAINS]->(Function|Class|Type)
(Function)-[:CALLS {call_site_line}]->(Function)
(File)-[:IMPORTS {import_path, is_dynamic}]->(File|Module)
(Class)-[:INHERITS]->(Class)
(Class)-[:IMPLEMENTS]->(Type)
(Package)-[:DEPENDS_ON {version_constraint}]->(Package)
(File)-[:DEFINES]->(Endpoint)
(Module)-[:EXPORTS {export_name}]->(Function|Class|Type)
(Function)-[:REFERENCES {usage_kind}]->(Type)
```

---

## Competitive Positioning

| Feature                    | Potpie             | Unlearn                  |
|----------------------------|--------------------|--------------------------|
| Graph DB                   | Neo4j              | Memgraph (in-memory, faster queries) |
| Interface                  | Own agents/UI/API  | MCP server (any client)  |
| LLM dependency             | Required (owns calls) | Optional (client's LLM) |
| Zero-infra mode            | No                 | Yes (CODEBASE.md)        |
| Incremental updates        | Full re-index      | AST-diff based           |
| Cross-repo graph           | Per-repo isolated  | Org-level topology       |
| Self-hostable              | Yes (complex setup) | Yes (docker compose)     |
| Distribution               | VS Code ext + API  | GitHub App + MCP + CLI   |
| Time to value              | Install + configure agents | `npx unlearn generate` (30 seconds) |
| Vendor lock-in             | High (their agents) | None (standard protocol + static files) |

---

## Milestones

### v0.1 — Static Mode + Proof of Concept (Weeks 1-3)
- [ ] tree-sitter parsing for Python + TypeScript
- [ ] In-memory graph construction (no Memgraph needed yet)
- [ ] `unlearn generate` CLI → outputs CODEBASE.md
- [ ] `.unlearn/knowledge.json` structured output
- [ ] Module purpose inference from graph structure (template-based, no LLM)
- [ ] File size budgeting (< 50KB target for CODEBASE.md)
- [ ] Publish as `npx unlearn` (npm) and `pip install unlearn-cli`

### v0.2 — Local Graph + MCP (Weeks 4-6)
- [ ] Memgraph schema + node/edge creation
- [ ] `unlearn serve` — local Memgraph + MCP server
- [ ] MCP server with `get_context`, `search_code`, `get_architecture` tools
- [ ] stdio transport (works with Claude Code locally)
- [ ] Streamable HTTP transport (localhost, for Cursor etc.)
- [ ] Go language support

### v0.3 — GitHub Integration (Weeks 7-9)
- [ ] GitHub App: OAuth + webhook receiver
- [ ] Repo cloning via installation tokens
- [ ] Full cloud indexing pipeline (clone → parse → graph)
- [ ] Remote MCP server (hosted, auth via JWT)
- [ ] `list_repos`, `trace_dependencies`, `impact_analysis` tools
- [ ] Basic dashboard (connected repos, indexing status)
- [ ] Incremental updates via push webhooks + AST diffing

### v0.4 — Cross-Repo + Enrichment (Weeks 10-12)
- [ ] Cross-repo edge detection (package deps, API contract matching)
- [ ] `get_org_topology` tool
- [ ] Cross-repo `impact_analysis` and `trace_dependencies`
- [ ] `unlearn generate --workspace` for multi-repo static mode + ORG_GRAPH.md
- [ ] LLM enrichment pipeline (docstring generation, optional)
- [ ] Embedding generation + semantic search
- [ ] `diff_context` and `query_graph` tools
- [ ] Rust + Java language support
- [ ] Confidence scoring on cross-repo edges

### v0.5 — Infrastructure Detection + Polish (Weeks 13-15)
- [ ] Shared resource detection (DB tables, queues, buckets)
- [ ] Schema file matching (protobuf, OpenAPI, GraphQL)
- [ ] MCP resources (passive context)
- [ ] Self-hosted Docker Compose distribution
- [ ] Rate limiting, usage metrics, error handling
- [ ] Documentation site

### v1.0 — Launch
- [ ] GitHub Marketplace listing
- [ ] Managed cloud offering
- [ ] Pricing tiers
- [ ] Integration guides for Claude Code, Cursor, Windsurf
- [ ] Landing page + docs at unlearn.dev

---

## Open Questions

1. **Language choice for MCP server:** Python (FastMCP, matches Memgraph's best client lib) vs TypeScript (MCP SDK is more mature, better for GitHub App ecosystem). Recommendation: **Python** — FastMCP is solid, tree-sitter has great Python bindings, and Memgraph's Python driver (GQLAlchemy) is the most feature-complete.

2. **Vector storage:** Memgraph doesn't have native vector indexing yet. Options: store embeddings as node properties and do brute-force similarity in application code (fine for <100k nodes), or run a Qdrant sidecar. Recommendation: **Start with in-app cosine similarity**, move to Qdrant when scale demands it.

3. **Multi-tenant isolation:** Database-per-user in Memgraph, or graph-per-user with `repo_id` filtering? Recommendation: **Property-based isolation** (`repo_id` on every node) for simplicity at launch, database-per-org for enterprise tier.

4. **Pricing model:** Free tier (1 repo, community), Pro (unlimited repos, faster indexing, managed enrichment), Enterprise (self-hosted, SSO, dedicated instance). Exact pricing TBD.

5. **Should `query_graph` be exposed?** Giving agents raw Cypher access is powerful but risky (slow queries, data leakage across repos). Recommendation: **Yes, but sandboxed** — read-only, query timeout, forced repo scoping, query complexity limits.

6. **CODEBASE.md naming and placement:** Should the static file be called `CODEBASE.md` (descriptive, clear), `UNLEARN.md` (branded), or something else like `.context/architecture.md`? Should it live in repo root (maximum visibility) or in `.unlearn/` (cleaner)? Recommendation: **`CODEBASE.md` in repo root** — it's descriptive, Claude Code / Cursor will auto-read root markdown files, and it doubles as human-readable documentation. The `.unlearn/knowledge.json` goes in a dotdir for structured tooling.

7. **Cross-repo edge staleness:** When repo A is re-indexed but repo B hasn't been, cross-repo edges involving B might be stale. How aggressively should we prune? Recommendation: **Soft-expire** — mark edges with a `last_verified_at` timestamp, include staleness info in MCP tool responses, let the consuming agent decide whether to trust stale edges.

8. **Static mode CI integration:** Should `unlearn generate` fail CI if CODEBASE.md is out of date (diff detected)? This would enforce keeping it current. Recommendation: **Optional strict mode** — `unlearn generate --check` returns exit code 1 if the file would change, suitable for CI. Default is just regenerate.
