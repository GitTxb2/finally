# FinAlly — AI Trading Workstation

## What This Is

A single-Docker simulated trading workstation built as a capstone for an agentic-AI coding course. It streams live ticker prices into a Bloomberg-style dark UI; the user trades a simulated $10,000 portfolio with market orders; and an AI chat assistant — with full auto-execute authority — analyzes positions, manages the watchlist, and places trades on the user's behalf. Per-ticker sentiment badges (LLM-generated) sit beside each ticker as an at-a-glance signal.

## Core Value

Demonstrates orchestrated AI coding agents producing a polished, demo-quality agentic-AI app — the AI chat agent's ability to take real action (trade, modify watchlist) without confirmation is the centerpiece of the story.

## Requirements

### Validated

<!-- Already shipped in the existing codebase (market-data slice). -->

- ✓ Pluggable market-data source abstraction (`MarketDataSource` ABC; simulator and Massive REST implementations selected by `MASSIVE_API_KEY`) — `backend/app/market/`
- ✓ GBM price simulator with sector-correlated moves (Cholesky decomposition, per-ticker μ/σ, random "event" shocks ~0.1%/tick) — `backend/app/market/simulator.py`
- ✓ Massive (Polygon.io) REST polling client with sync-SDK-on-thread offload — `backend/app/market/massive_client.py`
- ✓ Thread-safe in-memory `PriceCache` with monotonic version counter (the producer/consumer sync primitive) — `backend/app/market/cache.py`
- ✓ SSE router factory (`/api/stream/prices`) with disconnect detection and browser-retry hint — `backend/app/market/stream.py`
- ✓ Pytest + pytest-asyncio test suite for market subsystem (~70 tests; unit + async integration; Massive I/O mocked) — `backend/tests/market/`

### Active

<!-- Building toward these. Each maps to a phase in ROADMAP.md. -->

- [ ] FastAPI application root with `lifespan` wiring the `PriceCache` and `MarketDataSource` lifecycle, plus a mountable router for the market SSE endpoint
- [ ] SQLite persistence with lazy schema init (`db/finally.db`, volume-mounted) for `users_profile`, `watchlist`, `positions`, `trades`, `portfolio_snapshots`, `chat_messages`
- [ ] Portfolio API: `GET /api/portfolio`, `POST /api/portfolio/trade`, `GET /api/portfolio/history` — market orders only, instant fill, fractional shares
- [ ] Watchlist API: `GET/POST/DELETE /api/watchlist[/{ticker}]` with live-price hydration
- [ ] Background portfolio snapshotter (~30 s cadence + on-trade) for the P&L chart
- [ ] AI chat endpoint (`POST /api/chat`) with LiteLLM → OpenRouter → `openrouter/openai/gpt-oss-120b` via Cerebras, structured-output schema (`message`, `trades[]`, `watchlist_changes[]`), full auto-execute, mock-mode (`LLM_MOCK=true`)
- [ ] Per-ticker LLM-generated sentiment scoring (no real news source) with bullish/neutral/bearish badge — surfaced via API + cached for the watchlist hydration
- [ ] Next.js (TypeScript) frontend, static export, served by FastAPI: header (live portfolio total + connection dot), watchlist grid (price flash, sparkline, sentiment badge), main chart, portfolio heatmap (treemap), P&L line chart, positions table, trade bar, AI chat panel
- [ ] Multi-stage Dockerfile (Node build → Python runtime) serving everything on port 8000 with SQLite on a named volume
- [ ] Start/stop scripts for macOS/Linux (`scripts/start_mac.sh`, `stop_mac.sh`) and Windows (`scripts/start_windows.ps1`, `stop_windows.ps1`)
- [ ] Playwright E2E suite with `docker-compose.test.yml` and `LLM_MOCK=true` for deterministic agent behavior

### Out of Scope

<!-- Explicit exclusions inherited from the original spec; reasoning preserved. -->

- Authentication / multi-user — single user, hardcoded `user_id="default"`. Adding auth would add a database server, session handling, and password reset flows for zero demo benefit.
- Limit orders, stop-losses, partial fills, order book — market orders only. Keeps portfolio math trivial.
- Short selling, options, derivatives — out of scope. Long positions only.
- Real news fetching for sentiment — LLM generates sentiment from training-cutoff knowledge only. Avoids managing a second API integration and keeps the demo always-on.
- Real-time chat with other users — single user; no presence, no rooms.
- Mobile app — web-first, desktop-optimized layout.
- Production deployment / cloud infrastructure — local Docker is the target; a deploy stretch goal may exist but is not part of the demo bar.

## Context

- **Codebase state (2026-05-17):** The market-data subsystem (`backend/app/market/`) is built, tested, and merged. The rest of the platform — FastAPI entrypoint, persistence, portfolio logic, AI chat, frontend, Docker, scripts, E2E — does not exist yet. See `.planning/codebase/` for the full map.
- **Working-tree state:** `backend/pyproject.toml`, `backend/market_data_demo.py`, and the entire `planning/` directory are staged for deletion as part of the GSD reset. The `pyproject.toml` is needed by `uv` and must be restored or recreated before any backend phase executes (`.planning/codebase/CONCERNS.md` flags this).
- **Documentation drift:** Root `CLAUDE.md` still `@`-references `planning/PLAN.md` (deleted); `README.md` describes directories (`frontend/`, `db/`, `test/`, `scripts/`) that don't exist yet. Both will be regenerated by the GSD `$INSTRUCTION_FILE` step at the end of this workflow.
- **Original product brief:** Recoverable from git commit `38b3398` (`git show 38b3398:planning/PLAN.md`). It defines the feature set, the architecture choices (SSE over WebSockets, SQLite over Postgres, single-container deployment), the data schema, the API surface, and the LLM integration pattern. This `PROJECT.md` inherits all of that *except* the sentiment-badge addition.
- **Course context:** Built by orchestrated coding agents (i.e., this workflow) — the project is itself a meta-demonstration of the agentic-AI capabilities it ships.

## Constraints

- **Tech stack — Backend**: FastAPI on Python ≥3.12, managed by `uv` — Already chosen and partly built. Switching now wastes the market-data implementation and the test suite.
- **Tech stack — Frontend**: Next.js with TypeScript, built via `output: 'export'` static export, served as static files by FastAPI — Single-origin deployment, no CORS, one port, one container.
- **Tech stack — Persistence**: SQLite at `db/finally.db`, lazy-initialized — No auth means no multi-user means no need for a database server.
- **Tech stack — Real-time**: Server-Sent Events (SSE), not WebSockets — One-way push is all we need; simpler protocol, universal browser support, already implemented.
- **Tech stack — LLM**: LiteLLM → OpenRouter → `openrouter/openai/gpt-oss-120b` via the Cerebras provider, using structured outputs — Defined by the course's `.claude/skills/cerebras/SKILL.md` skill.
- **Deployment**: Single Docker container, exposed on port 8000, with a named volume for the SQLite file — Students run one command (no `docker-compose` for production, no service orchestration).
- **UX — Aesthetic**: Dark Bloomberg-terminal look. Accent yellow `#ecad0a`, primary blue `#209dd7`, submit-button purple `#753991`. Backgrounds around `#0d1117`/`#1a1a2e`. Price flash animations on tick (green/red, ~500 ms fade).
- **UX — Layout**: Desktop-first, dense, multi-pane; responsive but not mobile-optimized.
- **Demo timeline**: Course capstone deadline (date TBD by user) — coarse-grained phases over many fine-grained ones.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| AI chat agent has full auto-execute authority (trades + watchlist) — no confirmation dialog | Maximally agentic UX; this is the demo's centerpiece moment. Fake money + simulator = stakes are zero. | — Pending (validate during AI-chat phase) |
| Per-ticker sentiment is LLM-generated, no real news API | One fewer integration, demo always works regardless of `MASSIVE_API_KEY` state, course story is "AI infers sentiment-like output," not "real-time market intel." | — Pending |
| Inherit PLAN.md's architecture choices verbatim (SSE, SQLite, single container, market orders, single user) | The market-data slice was built against these assumptions; reusing them preserves that work. | ✓ Good (already shipped market-data slice on this foundation) |
| Pluggable `MarketDataSource` ABC with env-var selection | Lets simulator and Massive coexist; downstream code (SSE, portfolio, sentiment) never knows which source is live. | ✓ Good |
| Restore `backend/pyproject.toml` rather than re-create from scratch | The HEAD version captures pin choices (numpy 2.x, fastapi ≥0.115, ruff rule selection) that the existing code relies on; recreating risks divergence. | — Pending (must happen in Phase 1) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-17 after initialization*
