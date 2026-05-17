# Phase 1: Backend Boot + Streaming Hello-World - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-17
**Phase:** 1-Backend Boot + Streaming Hello-World
**Areas discussed:** Backend app structure, Phase 1 streaming tickers

---

## Backend app structure

### Q1 — Where should the FastAPI entrypoint live, and how should routers be organized?

| Option | Description | Selected |
|--------|-------------|----------|
| main.py + app/api/ package | `app/main.py` builds the FastAPI app, lifespan, static mount; `app/api/__init__.py` exports an `api_router` that aggregates per-concern routers (`health.py`, plus the existing market `stream.py`). Phases 2–9 each add 1–2 files under `app/api/`. | ✓ |
| Everything in main.py | Single file with `app = FastAPI()`, lifespan, health endpoint, mount calls. | |
| main.py + per-route modules at app/ root | Routers at `app/health.py`, `app/portfolio.py`, mirroring how `app/market/` already sits at the root. | |

**User's choice:** main.py + app/api/ package (Recommended)
**Notes:** Empty `app/api/` and `tests/api/` dirs already exist (only `__pycache__/` inside) — picking this layout slots into what was scaffolded.

---

### Q2 — Where does the singleton PriceCache live so it's accessible to routes and the lifespan task?

| Option | Description | Selected |
|--------|-------------|----------|
| app.state.price_cache | Lifespan sets `app.state.price_cache = PriceCache()`; routes access via `request.app.state.price_cache`. | ✓ |
| Module-level globals in app/main.py | Top-level `price_cache: PriceCache | None = None`; lifespan initializes; routes import the symbol. | |
| FastAPI Depends() | Dependency function returns the cache from app.state. | |

**User's choice:** app.state.price_cache (Recommended)
**Notes:** Standard FastAPI pattern; lifespan owns the instance lifecycle. Future routers can still wrap a `Depends()` helper on top if testing needs it.

---

### Q3 — How to reconcile `create_stream_router(price_cache)` (arg injection) with the app.state pattern?

| Option | Description | Selected |
|--------|-------------|----------|
| Keep stream.py as-is; build router inside lifespan | Inside lifespan startup, after creating the cache, call `app.include_router(create_stream_router(cache))`. | ✓ |
| Refactor stream.py to read from app.state | Change `create_stream_router` signature; generator reads `request.app.state.price_cache`. | |
| Build all routers from factory passed the cache | Every router uses `create_X_router(cache)`; no app.state. | |

**User's choice:** Keep stream.py as-is; build the router inside lifespan (Recommended)
**Notes:** Preserves the validated/tested market subsystem (MKT-V05). Lifespan is the natural place to wire it because the cache must exist first.

---

### Q4 — What should `GET /api/health` return?

| Option | Description | Selected |
|--------|-------------|----------|
| Status + source type + ticker count | `{status: "ok", source: "simulator"|"massive", tickers: <int>, cache_version: <int>}` | ✓ |
| Just status | `{status: "ok"}` | |
| Status + uptime + start time | `{status: "ok", uptime_seconds: <float>, started_at: <iso>}` | |

**User's choice:** Status + source type + ticker count (Recommended)
**Notes:** Useful for Docker HEALTHCHECK and the curl smoke test in success criteria #2. `cache_version` doubles as a "stream is alive" indicator without parsing SSE.

---

## Phase 1 streaming tickers

### Q5 — Which tickers should the SimulatorDataSource stream during Phase 1?

| Option | Description | Selected |
|--------|-------------|----------|
| All 10 defaults, UI renders AAPL only | Lifespan starts source with the full SEED_PRICES list; frontend filters to AAPL. | ✓ |
| Just AAPL | Lifespan starts source with `["AAPL"]` only. | |
| AAPL + small starter set (3-4) | E.g. AAPL, GOOGL, MSFT, NVDA. | |

**User's choice:** All 10 defaults, UI renders AAPL only (Recommended)
**Notes:** Phase 2's watchlist consumes the same already-running stream — no source restart, no `add_ticker()` cascade.

---

### Q6 — Where does the "default 10 tickers" list live?

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse SEED_PRICES.keys() from app.market.seed_prices | `default_tickers = list(SEED_PRICES.keys())` in lifespan. | ✓ |
| Hardcode the list in app/main.py | `DEFAULT_TICKERS = ["AAPL", ...]` at module level. | |
| Add a new public constant in app/market/__init__.py | Export `DEFAULT_TICKERS` from the market package. | |

**User's choice:** Reuse SEED_PRICES.keys() from app.market.seed_prices (Recommended)
**Notes:** Single source of truth. Phase 2's DB-09 seed reads the same constant.

---

### Q7 — How strict is "render only AAPL" on the frontend?

| Option | Description | Selected |
|--------|-------------|----------|
| Subscribe to all, render AAPL tile only | EventSource receives all 10; global store holds all 10; only AAPL tile component reads from store. | ✓ |
| Filter SSE client-side to AAPL | Drop other 9 on the client. | |
| Server-side filter the SSE | Add `?tickers=AAPL` to `/api/stream/prices`. | |

**User's choice:** Subscribe to all, render AAPL tile only (Recommended)
**Notes:** Phase 2 just adds more tile components reading the same store — no SSE-client work.

---

## Claude's Discretion

The user opted not to discuss these explicitly; Claude resolved with the choices below (recorded so they can be revisited):

- **Working-tree cleanup:** Restore `backend/pyproject.toml` from git HEAD; accept the `backend/market_data_demo.py` deletion and update `backend/CLAUDE.md` to remove the `## Demo` section. Let the `planning/*` deletions land as-is.
- **Frontend scope:** Minimal app-shell (header placeholder + main panel containing the AAPL tile), not a bare hello-world. Sets up Tailwind theme tokens + Next.js `app/` directory skeleton.
- **Static-files mount path:** Planner picks; standard pattern is mounting `StaticFiles(html=True)` last so `/api/*` routes resolve first.
- **Tailwind setup depth:** Configure brand palette as named tokens (`accent`, `primary`, `submit`, `bg-base`, `bg-elevated`) in `tailwind.config.ts`. CSS-vars layer optional.
- **Dev workflow:** Local-dev convenience (`uv run uvicorn` + `next dev`) is allowed but not required. Phase 1 validates against `docker build && docker run` per success criteria.

## Deferred Ideas

- SQLite schema, watchlist UI, sparklines, daily change %, sentiment badges, AI chat, portfolio APIs, start/stop scripts, docker-compose, Playwright, `.env.example`, root `CLAUDE.md` + `README.md` regen — all mapped to their assigned phases per ROADMAP.md. None re-scoped into Phase 1.
