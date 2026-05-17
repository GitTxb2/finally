# Walking Skeleton — FinAlly

**Phase:** 1
**Generated:** 2026-05-17

## Capability Proven End-to-End

A user opens `http://localhost:8000/` (served by `docker run`) and watches AAPL stream a live simulated price that flashes green/red ~2 times per second.

This proves the full Phase-1 stack works: simulator loop → `PriceCache` → SSE generator → `EventSource` → React state → DOM repaint with CSS transition.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Backend framework | FastAPI on Python ≥3.12, `uv` manages deps | Already partially built; switching wastes the validated `app/market/` slice. |
| Backend entrypoint | `backend/app/main.py` (single `app = FastAPI(...)` + `lifespan`) | Mountable from `uvicorn app.main:app`; lifespan is the canonical place for cache + source lifecycle. |
| Router layout | `app/api/` package; `app/api/__init__.py` exports `api_router` aggregating per-concern routers | Future phases each add one file under `app/api/`; `main.py` shape is stable. |
| Singleton state | `app.state.price_cache`, `app.state.market_source` | Standard FastAPI pattern; lifespan owns lifecycle; routes read via `request.app.state.*`. |
| Existing market module | `backend/app/market/` shipped — untouched by Phase 1 | `create_stream_router(cache)` keeps argument-injection signature; called inside lifespan after cache exists. |
| Default tickers | `list(SEED_PRICES.keys())` from `app.market.seed_prices` | Single source of truth for the 10-ticker canonical list across all phases. |
| Frontend framework | Next.js 14 App Router (TypeScript), `output: 'export'` | Static export → served as plain files by FastAPI → single-origin, no CORS, single container. |
| Frontend styling | Tailwind CSS with brand palette as named tokens | Brand tokens (`accent`, `primary`, `submit`, `bg-base`, `bg-elevated`) referenced everywhere — no hex sprinkled across components. |
| Price state | Client-side global store (React Context, or Zustand if planner picks) keyed by ticker | EventSource feeds the store; Phase 2 tile components read from the same store with zero SSE changes. |
| Data persistence | SQLite at `db/finally.db` (deferred to Phase 2) | Phase 1 reserves the named volume mount path (`/app/db`); schema + lazy-init land in Phase 2. |
| Deployment target | Single Docker container on port 8000; multi-stage build (Node → Python) | Students run one command. Stage 1 = `next build`; Stage 2 = `uv sync` + `uvicorn` + copies `frontend/out/` into the runtime image. |
| Directory layout | `backend/app/` (FastAPI), `frontend/` (Next.js), `db/` (volume mount), `Dockerfile` at repo root | Matches PROJECT.md's "Tech stack" constraints + ROADMAP Phase 12's documented layout. |

## Stack Touched in Phase 1

- [x] Project scaffold — FastAPI `main.py` (new), Next.js project (new), `pyproject.toml` restored, Tailwind configured, `Dockerfile` (new)
- [x] Routing — `/api/health`, `/api/stream/prices` (existing market router mounted), static-files mount at `/`
- [x] Data flow — `SimulatorDataSource` → `PriceCache` → SSE → `EventSource` → DOM (one real producer→consumer cycle proven end-to-end)
- [x] UI — single AAPL price tile, live updates, green/red flash effect (one real interactive element wired to the API)
- [x] Deployment — `docker build && docker run -p 8000:8000 -v finally-data:/app/db finally` serves the full stack on a single port

## Out of Scope (Deferred to Later Slices)

Anything below is **intentionally** absent from Phase 1; future phases own these. Reopening any of these in a Phase-1 revision is scope creep.

- SQLite schema, tables, lazy initialization, seed rows → Phase 2
- Watchlist UI (grid, sparklines, daily-change %, sentiment badges) → Phases 2 + 8
- Portfolio APIs, trade bar, positions table, header portfolio total → Phase 3
- Portfolio visuals (heatmap, P&L chart) → Phase 4
- Watchlist add/remove UI → Phase 5
- AI chat panel (read-only and auto-execute) → Phases 6 + 7
- Per-ticker sentiment badges → Phase 8
- Selected-ticker main chart → Phase 9
- `start_mac.sh` / `start_windows.ps1` / `docker-compose.yml` / `.env.example` → Phase 10
- Playwright E2E + `docker-compose.test.yml` → Phase 11
- Root `CLAUDE.md` regeneration, root `README.md` directory-layout fix → Phase 12
- mypy/pyright type checker, GitHub Actions for pytest/ruff → Out-of-scope v2 (per REQUIREMENTS.md)

## Subsequent Slice Plan

Every later phase adds **one** vertical slice on top of this skeleton without altering the architectural decisions above:

- Phase 2: User opens the app, sees the **full 10-ticker watchlist** with prices, daily change %, and sparklines (DB lazy-init, watchlist hydration).
- Phase 3: User can **buy/sell from a trade bar**; cash + positions + portfolio total update live.
- Phase 4: User sees a **portfolio heatmap and P&L chart**.
- Phase 5: User can **add/remove tickers** from the watchlist; source picks up the change live.
- Phase 6: User can **chat with the AI** about their portfolio (read-only — no auto-execute).
- Phase 7: The AI **auto-executes trades and watchlist changes** the user requests in chat.
- Phase 8: Each ticker shows a **bullish/neutral/bearish sentiment badge** (LLM-generated, cached).
- Phase 9: Clicking a ticker opens a **larger detail chart** in the main area.
- Phase 10: One-command `start`/`stop` scripts work on macOS / Linux / Windows.
- Phase 11: **Playwright E2E suite** with `LLM_MOCK=true` covers the demo flows.
- Phase 12: Documentation reconciled — root `CLAUDE.md`, `README.md`, `backend/CLAUDE.md` match reality.
