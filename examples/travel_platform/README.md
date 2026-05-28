# travel-platform

A synthetic "enterprise" travel-booking codebase for exercising Unlearn at scale.

It is **structural-only**: imports resolve, calls land on real symbols, classes inherit from real bases — but the code is not meant to run end-to-end. The point is to give Unlearn something realistic to index so you can see what `impact_analysis`, `find_circular_dependencies`, `find_dead_code`, and `find_hotspots` return on a non-trivial codebase.

## Shape

```
travel_platform/
├── libs/travel_common/         # shared Python lib (currency, models, logging, errors, http)
├── services/                   # 7 Python FastAPI services
│   ├── search-svc       booking-svc      pricing-svc      inventory-svc
│   ├── user-svc         loyalty-svc      payments-svc
├── packages/ts-common/         # shared TS types + service clients
├── node-services/              # 3 TS/Node services
│   ├── gateway-bff             # BFF for the frontend
│   ├── notification-svc        # email / SMS / push
│   └── analytics-svc           # event ingest
├── frontend/                   # Next.js web app
└── infra/                      # Terraform modules + envs
    ├── modules/{vpc,rds,ecs-service,s3-bucket,iam-role}
    └── envs/{dev,staging,prod}
```

About 270 files. Python and TypeScript get indexed; Terraform is included for visual realism (v0.1 doesn't parse HCL).

## Planted scenarios

Four real structural patterns are deliberately seeded into the codebase so the MCP tools have something meaningful to find. Knowing where they are lets you sanity-check Unlearn's output.

### 1. Cross-service rename target (= the hotspot)

**Entity:** `format_currency(amount, code, options=None)` in `libs/travel_common/travel_common/currency.py`.

This is the canonical money formatter. It's imported and called from at least eight sites across five services:

| Service        | File                                                  |
|----------------|-------------------------------------------------------|
| pricing-svc    | `app/routes/prices.py`, `app/routes/discounts.py`, `app/services/pricing.py`, `app/services/discounts.py` |
| booking-svc    | `app/handlers/confirm.py`, `app/services/itinerary.py` |
| payments-svc   | `app/routes/charges.py`, `app/routes/refunds.py`, `app/services/charges.py`, `app/services/refunds.py` |
| loyalty-svc    | `app/routes/redemption.py`, `app/services/redemption.py` |
| search-svc     | `app/services/results.py`                              |

Try: `impact_analysis` on `format_currency` should return every site above. `find_hotspots` should rank it (and `get_logger` from `travel_common/logging.py`, imported by nearly every module) near the top.

### 2. Hidden 3-hop import cycle

In `node-services/gateway-bff/`, the auth and rate-limit layers form a circular dependency:

```
src/auth/session.ts          (createSession needs the rate-limit bucket)
   ↓ imports getRateLimitBucket from
src/middleware/rateLimit.ts  (rate limit depends on caller permissions)
   ↓ imports getPermissions from
src/auth/permissions.ts      (permissions are derived from the session)
   ↓ imports getSession from
src/auth/session.ts          (back where we started)
```

Try: `find_circular_dependencies` should surface this cycle. It is the only cycle in the fixture.

### 3. Dead code

| Where                                                                  | Why it's dead                                |
|------------------------------------------------------------------------|----------------------------------------------|
| `services/booking-svc/app/legacy/v1_handlers.py`                       | Whole module — replaced by `app/handlers/`   |
| `services/booking-svc/app/legacy/v1_validators.py`                     | Same                                         |
| `services/pricing-svc/app/utils/legacy_rounding.py`                    | Orphan helper — superseded by `rounding.py`  |
| `node-services/notification-svc/src/legacy/smsV1Client.ts`             | Old SMS gateway — replaced by `channels/smsClient.ts` |

Try: `find_dead_code` should surface every function in these files.

### 4. Hotspot

Same as scenario 1 — `format_currency` is the clearest winner. Secondary hotspots: `get_logger` (in `travel_common/logging.py`, imported by every Python module) and `ServiceClient` (in `travel_common/http.py`, used by every inter-service client).

## Indexing it

From the Unlearn repo root:

```bash
uv run unlearn index examples/travel_platform
uv run unlearn info  examples/travel_platform
```

The graph cache lands at `examples/travel_platform/.unlearn/graph.json`.

To wire the MCP server into Claude Code for this fixture, drop a `.mcp.json` in `examples/travel_platform/` with the standard server stanza from the top-level README.

## Why a fixture this size

Unlearn earns its keep on long-horizon agent tasks: refactors that touch many services, audits across a sprawling codebase, dependency tracing that an agent would otherwise re-grep on every turn. A 270-file multi-stack repo makes those tasks expensive enough by hand that the graph's value shows up clearly — and small enough that you can still hold the planted scenarios in your head while you verify the answers.
