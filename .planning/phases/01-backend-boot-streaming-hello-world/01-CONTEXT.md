# Phase 1: Backend Boot + Streaming Hello-World - Context

**Gathered:** 2026-05-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Stand up the FastAPI application root, wire the existing `backend/app/market/` subsystem into a live SSE stream, scaffold a minimal Next.js frontend that consumes the stream, and produce a working multi-stage Dockerfile. End state: `docker build && docker run -p 8000:8000 finally` serves a browser page at `http://localhost:8000/` that shows AAPL streaming a live price (~2 updates/sec) with a green/red flash on each tick.

**In scope:** FastAPI entrypoint + lifespan + cache wiring; `/api/health`; SSE router mount; static-files mount for the Next.js export; Next.js project with Tailwind brand theme + EventSource client + AAPL tile + price-flash effect; multi-stage Dockerfile; restoration of `backend/pyproject.toml`; named SQLite volume mount (path only — DB schema is Phase 2).

**Out of scope:** SQLite schema, watchlist UI, additional ticker tiles, portfolio APIs, AI chat, sentiment, start/stop scripts, docker-compose, Playwright. Those land in their assigned phases per ROADMAP.md.

</domain>

<decisions>
## Implementation Decisions

### Backend App Structure
- **D-01:** Entrypoint is `backend/app/main.py` — builds the `FastAPI` instance, defines the `lifespan` async context manager, mounts routers, mounts static files.
- **D-02:** Per-concern routers live under `backend/app/api/` as a package (`app/api/__init__.py` exports an `api_router: APIRouter` that aggregates child routers). Phase 1 adds `app/api/health.py`. Phases 2–9 add new modules under the same `app/api/` package — `main.py` does not change shape across phases.
- **D-03:** Singleton state (`PriceCache`, `MarketDataSource`) lives on `app.state`. Lifespan startup sets `app.state.price_cache = PriceCache()` and `app.state.market_source = create_market_data_source(cache)`, then `await source.start(default_tickers)`. Lifespan shutdown calls `await app.state.market_source.stop()`. Routes read state via `request.app.state.<attr>`.
- **D-04:** Do **not** modify `backend/app/market/stream.py`. `create_stream_router(price_cache)` keeps its existing argument-injection signature. Inside lifespan startup, after the cache exists, call `app.include_router(create_stream_router(app.state.price_cache))`. The shipped/tested market subsystem stays untouched.
- **D-05:** `GET /api/health` returns `{"status": "ok", "source": "<simulator|massive>", "tickers": <int>, "cache_version": <int>}`. Values are pulled from `app.state` — `source` is derived from `type(app.state.market_source).__name__` mapped to a short label, `tickers` is `len(app.state.price_cache.get_all())`, `cache_version` is `app.state.price_cache.version`. Implemented as `app/api/health.py`.

### Phase 1 Streaming Tickers
- **D-06:** The simulator starts with **all 10 default tickers** — AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX. Phase 2 (watchlist) consumes the same stream without restarting the source.
- **D-07:** The "default tickers" list is sourced from `app.market.seed_prices.SEED_PRICES.keys()`, materialized as `list(SEED_PRICES.keys())` inside lifespan startup. Single source of truth; Phase 2's DB seed (DB-09) will read the same constant. Do **not** hardcode the list in `main.py`.
- **D-08:** Frontend `EventSource` subscribes to the full stream and stores every incoming `PriceUpdate` in a global price store (e.g. Zustand or a React context — planner's call). The Phase 1 UI renders **only** the AAPL tile, reading AAPL out of the store. Phase 2 will add more tiles that read the same store — zero SSE-client churn.
- **D-09:** No server-side ticker filtering on the SSE endpoint. `stream.py` stays unchanged.

### Claude's Discretion
- **Working-tree cleanup:** Restore `backend/pyproject.toml` from git HEAD (Key Decision in PROJECT.md). Accept the `backend/market_data_demo.py` deletion and update `backend/CLAUDE.md` to remove the `## Demo` section that references it (CONCERNS.md flags this drift). The `planning/` directory deletions can land as-is — that wipe was intentional for the GSD reset.
- **Frontend scope:** Minimal app-shell scaffold — a header placeholder (brand color block with the app title) plus a main panel containing the single AAPL tile. Sets up Tailwind theme tokens + the `app/page.tsx` / `app/layout.tsx` skeleton so Phase 2 can drop the watchlist grid into the main panel without restructuring. No collapsible chat sidebar yet; no nav.
- **Static-files mount path:** Planner picks where the Next.js `out/` directory lands in the runtime image (likely `backend/static/` copied in by the Dockerfile's stage 2) and how `app.mount("/", StaticFiles(...))` is wired so it does **not** shadow `/api/*`. Standard pattern: mount static files last with `html=True`.
- **Tailwind setup depth:** Configure `tailwind.config.ts` with the brand palette as named tokens (`accent`, `primary`, `submit`, `bg-base`, `bg-elevated`) so future phases reference semantic names, not hex. CSS-vars layer is not required for Phase 1 but can be added if the planner judges it low-cost.
- **Dev workflow:** Phase 1's only validation surface is `docker build && docker run` per the success criteria. A local-dev convenience (`uv run uvicorn ...` + `next dev`) is allowed but not required; if added, document in `backend/CLAUDE.md` and (eventually) the root `README.md`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` §"Phase 1: Backend Boot + Streaming Hello-World" — Goal + 5 numbered success criteria.
- `.planning/REQUIREMENTS.md` §"Backend Foundation" (APP-01..06), §"Frontend Shell" (FE-01..04, FE-06), §"Packaging & Deployment" (PKG-01, PKG-03) — Phase 1's required items.
- `.planning/PROJECT.md` §"Constraints" + §"Key Decisions" — locked tech stack, brand palette, restore-pyproject-toml decision.

### Existing code (already shipped — do not modify)
- `backend/app/market/__init__.py` — public API surface (`PriceCache`, `PriceUpdate`, `MarketDataSource`, `create_market_data_source`, `create_stream_router`).
- `backend/app/market/interface.py` — `MarketDataSource` ABC and its lifecycle contract (`start`, `stop`, `add_ticker`, `remove_ticker`).
- `backend/app/market/factory.py` — env-var-driven selection (`MASSIVE_API_KEY`); shows the construction call pattern lifespan must use.
- `backend/app/market/seed_prices.py` — `SEED_PRICES` dict (canonical 10-ticker list).
- `backend/app/market/stream.py` — `create_stream_router(price_cache)` signature; SSE generator behavior incl. `retry: 1000` hint and disconnect detection.
- `backend/CLAUDE.md` — Backend developer guide; lists market public API and (currently) references the deleted `market_data_demo.py`.

### Codebase intel
- `.planning/codebase/STACK.md` — Languages, pins, package management. Authoritative dependency table.
- `.planning/codebase/ARCHITECTURE.md` — Layering and producer-cache-consumer pattern.
- `.planning/codebase/STRUCTURE.md` — File layout + pending working-tree deletions table.
- `.planning/codebase/CONVENTIONS.md` — Type hints, async/threading patterns, logging, rounding rules.
- `.planning/codebase/CONCERNS.md` — Working-tree hazards (`pyproject.toml`, `market_data_demo.py`), SSE-untested-route warning, no-application-root gap.
- `.planning/codebase/TESTING.md` — Test layout + style; relevant for the per-phase Definition of Done unit tests.

### LLM / external skills (referenced but not exercised in Phase 1)
- `.claude/skills/cerebras/SKILL.md` — LiteLLM + OpenRouter + Cerebras pattern (Phase 6 will exercise; not Phase 1).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PriceCache` (`backend/app/market/cache.py:11`) — thread-safe; `.version` is the monotonic counter the SSE generator already watches. Phase 1 hands the instance to both the data source and the SSE router.
- `create_market_data_source(cache)` (`backend/app/market/factory.py`) — already env-aware; lifespan calls it once.
- `create_stream_router(price_cache)` (`backend/app/market/stream.py`) — already implements SSE with `retry: 1000` initial chunk and version-change suppression. Phase 1 mounts it as-is.
- `SEED_PRICES` constant (`backend/app/market/seed_prices.py`) — 10-ticker canonical list, reused for both lifespan startup and (later) DB seed.

### Established Patterns
- **Async lifecycle convention:** every `MarketDataSource` method (`start`, `stop`, `add_ticker`, `remove_ticker`) is async even when no I/O awaits, for interface consistency. Lifespan must `await` them.
- **`stop()` idempotency:** the shipped sources guarantee double-`stop()` is a no-op. Lifespan shutdown can call it unconditionally.
- **Producer–Cache–Consumer decoupling:** Phase 1 must not let `main.py` (consumer-side) reach into the data source directly. Read from the cache; write happens inside the source's loop.
- **Module-level `from __future__ import annotations` everywhere; PEP 604 unions; `logging.getLogger(__name__)`; UPPER_SNAKE constants** — applies to new `app/main.py` and `app/api/*.py`.
- **`@dataclass(frozen=True, slots=True)` for value objects; plain classes for services** — Phase 1 has no new value objects yet (deferred to Phase 2's DB models).

### Integration Points
- `app/main.py` → `app.state.price_cache` (PriceCache instance)
- `app/main.py` → `app.state.market_source` (factory-selected source, started in lifespan)
- `app/main.py` → `app.include_router(create_stream_router(app.state.price_cache))` after cache exists
- `app/main.py` → `app.include_router(api_router, prefix="/api")` where `api_router` is `app/api/__init__.py`'s aggregator
- `app/api/health.py` → reads `request.app.state.price_cache` and `request.app.state.market_source`
- `app/main.py` → `app.mount("/", StaticFiles(directory="static", html=True), name="frontend")` — mounted **last** so `/api/*` routes resolve first
- **Dockerfile stage 2:** copies `frontend/out/` into the runtime image at the path FastAPI mounts

</code_context>

<specifics>
## Specific Ideas

- Default ticker list is `list(SEED_PRICES.keys())` — not hardcoded anywhere else.
- Health payload includes `cache_version` (monotonic counter from `PriceCache`) so smoke tests can observe the stream is alive without parsing SSE.
- Phase 1 Dockerfile already implies stage 1 = Node (for `next build`) → stage 2 = Python (for `uv sync` + `uvicorn`). Final image runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- Static export means **no Next.js server runtime in production** — only the static `out/` directory is shipped. Tailwind compiles at build time.

</specifics>

<deferred>
## Deferred Ideas

- SQLite schema + lazy-init + watchlist seed → Phase 2 (DB-01..04, DB-09).
- Multiple ticker tiles, sparklines, daily change %, sentiment badges → Phase 2 + Phase 8.
- `start_mac.sh` / `start_windows.ps1` / `docker-compose.yml` → Phase 10 (PKG-04..06).
- `.env.example` → Phase 10 (PKG-02). For Phase 1, env vars are documented in `backend/CLAUDE.md` only.
- Playwright E2E → Phase 11. Phase 1's only end-to-end validation is the manual smoke test in success criteria.
- Removing the stale `@planning/PLAN.md` reference from root `CLAUDE.md` and the directory-layout drift in `README.md` → Phase 12 (DOC-01, DOC-02). Phase 1 only touches `backend/CLAUDE.md`.
- Type checker (mypy/pyright) → not scoped. CONCERNS.md flags as future work.

</deferred>

---

*Phase: 01-backend-boot-streaming-hello-world*
*Context gathered: 2026-05-17*
