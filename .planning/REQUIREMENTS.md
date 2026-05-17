# Requirements: FinAlly

**Defined:** 2026-05-17
**Core Value:** Demonstrates orchestrated AI coding agents producing a polished, demo-quality agentic-AI app — the AI chat agent's ability to take real action (trade, modify watchlist) without confirmation is the centerpiece of the story.

## Validated (Already Shipped)

These came in with the existing market-data subsystem (`backend/app/market/`). They are not in `## v1 Requirements` below because they're already done; they're listed here so traceability is honest.

- ✓ **MKT-V01**: Pluggable `MarketDataSource` abstract interface with env-var-driven selection (`backend/app/market/interface.py`, `factory.py`)
- ✓ **MKT-V02**: GBM price simulator with sector-correlated Cholesky moves and per-ticker μ/σ (`backend/app/market/simulator.py`, `seed_prices.py`)
- ✓ **MKT-V03**: Massive (Polygon.io) REST client with sync-SDK-on-thread offload (`backend/app/market/massive_client.py`)
- ✓ **MKT-V04**: Thread-safe in-memory `PriceCache` with monotonic version counter (`backend/app/market/cache.py`)
- ✓ **MKT-V05**: SSE router factory (`/api/stream/prices`) with disconnect detection and browser-retry hint (`backend/app/market/stream.py`)
- ✓ **MKT-V06**: Pytest + pytest-asyncio test suite for market subsystem (~70 tests)

## v1 Requirements

### Backend Foundation

- [ ] **APP-01**: FastAPI application root (`backend/app/main.py`) exposing a single ASGI `app` instance
- [ ] **APP-02**: `lifespan` async context manager that constructs the singleton `PriceCache`, instantiates the env-selected `MarketDataSource` via `create_market_data_source(cache)`, calls `await source.start(default_tickers)`, and `await source.stop()` on shutdown
- [ ] **APP-03**: Application mounts the SSE router (`create_stream_router(cache)`) and all REST routers under `/api/*`
- [ ] **APP-04**: `GET /api/health` returns `200 OK` with a small JSON status payload (for Docker health-check and smoke tests)
- [ ] **APP-05**: Static-files mount serves the built Next.js export at `/` so the same origin serves UI and API
- [ ] **APP-06**: `backend/pyproject.toml` and `uv.lock` are present and lock dependencies (restore from git HEAD if working-tree deletion lands)

### Persistence

- [ ] **DB-01**: SQLite database file at `db/finally.db` (path overridable via env var), volume-mounted in Docker
- [ ] **DB-02**: Lazy schema initialization on first request — creates tables and seeds default data if file is missing or tables empty
- [ ] **DB-03**: `users_profile` table (`id` PK default `"default"`, `cash_balance` REAL default `10000.0`, `created_at`)
- [ ] **DB-04**: `watchlist` table (`id` UUID PK, `user_id`, `ticker`, `added_at`, UNIQUE(`user_id`, `ticker`))
- [ ] **DB-05**: `positions` table (`id` UUID PK, `user_id`, `ticker`, `quantity` REAL, `avg_cost` REAL, `updated_at`, UNIQUE(`user_id`, `ticker`))
- [ ] **DB-06**: `trades` table (`id` UUID PK, `user_id`, `ticker`, `side` `"buy"`/`"sell"`, `quantity`, `price`, `executed_at`) — append-only
- [ ] **DB-07**: `portfolio_snapshots` table (`id` UUID PK, `user_id`, `total_value`, `recorded_at`)
- [ ] **DB-08**: `chat_messages` table (`id` UUID PK, `user_id`, `role` `"user"`/`"assistant"`, `content`, `actions` JSON nullable, `created_at`)
- [ ] **DB-09**: Default seed inserts one `users_profile` row and ten default watchlist tickers: AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX

### Portfolio

- [ ] **PORT-01**: `GET /api/portfolio` returns current cash, positions (with live price, unrealized P&L, %), total portfolio value
- [ ] **PORT-02**: `POST /api/portfolio/trade` body `{ticker, quantity, side}` — instant-fill at the live cache price; debits/credits cash; updates/creates/removes the position row; appends a `trades` row; takes a fresh `portfolio_snapshots` row
- [ ] **PORT-03**: Trade validation — reject buy on insufficient cash; reject sell on insufficient shares; reject unknown ticker (not in the cache); reject non-positive quantity. Return a JSON error with a human-readable message.
- [ ] **PORT-04**: Fractional shares supported throughout (REAL quantities, average-cost math handles fractions)
- [ ] **PORT-05**: `GET /api/portfolio/history` returns the `portfolio_snapshots` rows for the user (newest-first, optional limit)
- [ ] **PORT-06**: Background task records a `portfolio_snapshots` row every 30 seconds while the app is running

### Watchlist

- [ ] **WL-01**: `GET /api/watchlist` returns the user's watchlist rows hydrated with the latest price (from `PriceCache`) and the per-ticker sentiment badge
- [ ] **WL-02**: `POST /api/watchlist` body `{ticker}` — normalizes (upper-case, trim), inserts into the `watchlist` table, calls `source.add_ticker(t)` so the data source begins producing prices for it
- [ ] **WL-03**: `DELETE /api/watchlist/{ticker}` — removes the watchlist row and calls `source.remove_ticker(t)`
- [ ] **WL-04**: Watchlist operations reject duplicates and invalid ticker formats with JSON errors

### AI Chat

- [ ] **CHAT-01**: `POST /api/chat` body `{message}` — assembles the LLM context (system prompt, portfolio snapshot, recent `chat_messages` history, user message), calls LiteLLM → OpenRouter → `openrouter/openai/gpt-oss-120b` via the Cerebras provider (per `.claude/skills/cerebras/SKILL.md`) with structured outputs
- [ ] **CHAT-02**: Structured output schema enforced: `{message: str, trades: [{ticker, side, quantity}]?, watchlist_changes: [{ticker, action}]?}`
- [ ] **CHAT-03**: Any `trades` in the LLM response are auto-executed via the same validation path as `POST /api/portfolio/trade` — no confirmation dialog
- [ ] **CHAT-04**: Any `watchlist_changes` in the LLM response are auto-executed via the same validation path as `POST /api/watchlist`
- [ ] **CHAT-05**: Failed actions (validation errors) are captured and surfaced both in the API response and back into the next LLM turn so the agent can apologize/explain
- [ ] **CHAT-06**: Chat user message + assistant response + executed `actions` are persisted to `chat_messages` (assistant `actions` field stores the JSON action list)
- [ ] **CHAT-07**: `LLM_MOCK=true` env var swaps LiteLLM out for a deterministic mock that returns canned structured responses driven by message-content matching (for E2E and CI)

### Sentiment

- [ ] **SENT-01**: `GET /api/sentiment/{ticker}` returns `{ticker, score: bullish|neutral|bearish, summary: str, generated_at}` — LLM-generated, no real news source
- [ ] **SENT-02**: Sentiment is cached server-side with a TTL (configurable, default 5 min) to avoid hitting the LLM on every watchlist hydration
- [ ] **SENT-03**: Watchlist hydration (`GET /api/watchlist`) includes the per-ticker sentiment badge inline; missing-from-cache tickers trigger a background refresh and return `unknown` until ready
- [ ] **SENT-04**: Sentiment scoring respects `LLM_MOCK=true` and returns deterministic mock values per ticker for E2E tests

### Frontend Shell

- [ ] **FE-01**: Next.js (TypeScript) project under `frontend/`, configured with `output: 'export'` for static export
- [ ] **FE-02**: Tailwind CSS configured with a custom dark theme using the brand palette (`#0d1117`/`#1a1a2e` backgrounds, accent yellow `#ecad0a`, primary blue `#209dd7`, submit-button purple `#753991`)
- [ ] **FE-03**: All API calls target same-origin `/api/*` paths — no CORS configuration
- [ ] **FE-04**: SSE client (`EventSource`) connects to `/api/stream/prices`, parses incoming JSON, updates a global price store, handles auto-reconnect (browser-native)
- [ ] **FE-05**: Header bar — portfolio total value (updates live from prices + positions), connection status dot (green/yellow/red), cash balance, app title
- [ ] **FE-06**: Price flash effect — receiving a new price applies a green/red background class via CSS transition that fades over ~500 ms

### Frontend Components

- [ ] **FE-07**: Watchlist grid — ticker symbol, current price (with flash), daily change %, sparkline accumulated client-side from the SSE stream since page load, sentiment badge. Click selects ticker for main chart.
- [ ] **FE-08**: Main chart — larger price-over-time chart for the selected ticker (canvas-based; Lightweight Charts or Recharts)
- [ ] **FE-09**: Portfolio heatmap — treemap where each rectangle is a position, sized by portfolio weight, colored by P&L (green→profit, red→loss)
- [ ] **FE-10**: P&L line chart — total portfolio value over time, fed by `/api/portfolio/history`
- [ ] **FE-11**: Positions table — ticker, quantity, avg cost, current price, unrealized P&L, % change; live-updating
- [ ] **FE-12**: Trade bar — ticker input, quantity input, Buy / Sell buttons (purple for submit). Market orders, instant fill. Surfaces validation errors inline.
- [ ] **FE-13**: AI chat panel — docked / collapsible sidebar; scrolling message history; input box with submit; loading indicator while waiting for the LLM; trade and watchlist actions rendered inline as confirmation chips inside the assistant message
- [ ] **FE-14**: Add-ticker / remove-ticker UI in the watchlist panel (button → input, or context menu) wired to the watchlist API

### Packaging & Deployment

- [ ] **PKG-01**: Multi-stage `Dockerfile` — Stage 1 (Node 20-slim) builds the Next.js static export; Stage 2 (Python 3.12-slim) installs `uv`, syncs deps from `backend/pyproject.toml`/`uv.lock`, copies the Next.js build output into a `static/` directory, runs `uvicorn` serving the FastAPI app on port 8000
- [ ] **PKG-02**: `.env.example` committed at project root listing all env vars (`OPENROUTER_API_KEY`, `MASSIVE_API_KEY`, `LLM_MOCK`)
- [ ] **PKG-03**: Single named Docker volume (`finally-data`) mounts at `/app/db` for SQLite persistence across container restarts
- [ ] **PKG-04**: `scripts/start_mac.sh` and `scripts/stop_mac.sh` — idempotent build-and-run / stop-without-volume-removal for macOS/Linux
- [ ] **PKG-05**: `scripts/start_windows.ps1` and `scripts/stop_windows.ps1` — PowerShell equivalents
- [ ] **PKG-06**: `docker-compose.yml` (optional convenience wrapper for the same single-container run)

### Testing

- [ ] **TEST-01**: Backend test coverage extended to cover the new modules: portfolio endpoints, watchlist endpoints, chat endpoint (mock-mode), sentiment endpoint (mock-mode), DB lazy-init, SSE generator
- [ ] **TEST-02**: Frontend unit tests for component rendering, price-flash effect, watchlist CRUD, chat panel render states
- [ ] **TEST-03**: `test/docker-compose.test.yml` spins up the app container + a Playwright container with `LLM_MOCK=true`
- [ ] **TEST-04**: Playwright E2E scenarios — fresh start (default watchlist + $10k), add/remove a ticker, buy/sell (cash and position update), portfolio visualization renders, AI chat sends and gets a structured response with auto-executed trade inline, SSE reconnects after a forced disconnect

### Project Hygiene

- [ ] **DOC-01**: Root `CLAUDE.md` regenerated by GSD's `generate-claude-md` to remove the stale `@planning/PLAN.md` reference and reflect the new `.planning/` layout
- [ ] **DOC-02**: Root `README.md` updated so the documented directory layout (frontend, db, test, scripts) matches reality, with quick-start instructions that actually work
- [ ] **DOC-03**: `backend/CLAUDE.md` updated if `market_data_demo.py` deletion lands (remove the demo reference) or restored if the demo is kept

## v2 Requirements

Deferred. Tracked here so they're not forgotten but not in v1's roadmap.

### Real Sentiment

- **SENT2-01**: Replace LLM-only sentiment with real news fetching (Massive news endpoint or free news API)
- **SENT2-02**: Per-ticker recent-headlines panel surfaced in the ticker detail view

### Operations

- **OPS2-01**: GitHub Actions workflow that runs `pytest` and `ruff` on every PR (currently only Claude-bot workflows exist)
- **OPS2-02**: Cloud deployment artifact (AWS App Runner Terraform, Render `render.yaml`, or Fly.io `fly.toml`) — stretch goal from PLAN.md

### Demo Polish

- **POL2-01**: Onboarding tour / first-run tooltips
- **POL2-02**: Configurable starting cash / starting positions for demos

## Out of Scope

Explicit exclusions; reasoning preserved so they don't get reintroduced silently.

| Feature | Reason |
|---------|--------|
| Authentication / multi-user / sign-up | Single-user demo; hardcoded `user_id="default"`. Adding auth means session handling, password reset, DB user table — zero demo benefit. |
| Limit orders, stop-losses, partial fills, order book | Market orders only — keeps portfolio math trivial. |
| Short selling, options, derivatives | Long positions only — out of demo scope. |
| Real news API for sentiment (v1) | LLM-generated sentiment chosen to keep the demo always-on regardless of `MASSIVE_API_KEY`. Reconsidered in v2. |
| Real-time chat between users | Single user; no presence, no rooms. |
| Mobile app / mobile-optimized layout | Web-first, desktop-optimized. Functional on tablet but not the target. |
| Production cloud deployment | Local Docker is the demo target. Cloud is a v2 stretch. |
| Trade confirmation dialog (for AI agent actions) | Full auto-execute is intentional — it's the agentic-AI centerpiece. |
| Multiple watchlists per user | One watchlist, hardcoded user. |

## Traceability

Filled in during roadmap creation. Empty until ROADMAP.md lands.

| Requirement | Phase | Status |
|-------------|-------|--------|
| APP-01..06  | TBD   | Pending |
| DB-01..09   | TBD   | Pending |
| PORT-01..06 | TBD   | Pending |
| WL-01..04   | TBD   | Pending |
| CHAT-01..07 | TBD   | Pending |
| SENT-01..04 | TBD   | Pending |
| FE-01..14   | TBD   | Pending |
| PKG-01..06  | TBD   | Pending |
| TEST-01..04 | TBD   | Pending |
| DOC-01..03  | TBD   | Pending |

**Coverage:**
- v1 requirements: 56 total (across 10 categories)
- Mapped to phases: 0 (pending roadmap)
- Unmapped: 56 ⚠️ (will be 0 after ROADMAP.md is written)

---
*Requirements defined: 2026-05-17*
*Last updated: 2026-05-17 after initialization*
