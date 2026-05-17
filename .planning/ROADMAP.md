# Roadmap: FinAlly

**Created:** 2026-05-17
**Mode:** Vertical MVP
**Granularity:** Fine (12 phases)

Each phase delivers an end-to-end, demoable capability — `docker run` should produce something a user can interact with at every phase boundary. The market-data subsystem (`backend/app/market/`) is already built and is treated as a reusable dependency, not as a phase.

---

## Phase Overview

| # | Phase | Goal | Requirements |
|---|-------|------|--------------|
| 1 | Backend Boot + Streaming Hello-World | One ticker price streams to a browser in Docker | APP-01..06, FE-01..06 (subset), PKG-01..03 (minimal) |
| 2 | Watchlist Display | Default 10-ticker watchlist visible, prices flashing, sparklines drawing | DB-01..04, DB-09, WL-01, FE-07 |
| 3 | Trading | User can buy/sell from the UI; cash + positions update | DB-05..06, PORT-01..04, FE-05 (live total), FE-11, FE-12 |
| 4 | Portfolio Visuals | Heatmap + P&L chart show portfolio shape and history | DB-07, PORT-05..06, FE-09, FE-10 |
| 5 | Watchlist Management | User can add/remove tickers manually | WL-02..04, FE-14 |
| 6 | AI Chat — Read-Only | User can converse with the LLM about their portfolio | DB-08, CHAT-01, CHAT-02 (analysis-only), CHAT-06..07, FE-13 (render only) |
| 7 | AI Chat — Auto-Execute | LLM auto-executes trades and watchlist changes | CHAT-03..05, FE-13 (action chips) |
| 8 | Sentiment Badges | Each ticker shows an LLM-inferred sentiment badge in the watchlist | SENT-01..04, FE-07 (badge slot) |
| 9 | Selected Ticker Chart | Clicking a ticker opens a detail chart in the main area | FE-08 |
| 10 | Packaging Polish | One-command start/stop on macOS, Linux, and Windows | PKG-04..06, PKG-02 |
| 11 | E2E Testing | Automated Playwright suite covers the key demo flows | TEST-03..04 |
| 12 | Docs & Reconciliation | Project documentation reflects reality | DOC-01..03 |

**Cross-cutting:** Each phase is responsible for backend unit tests covering its new modules (TEST-01) and frontend unit tests for its new components (TEST-02). These are part of each phase's Definition of Done, not a separate phase.

**Coverage:** All 56 v1 requirements are mapped to a phase. Validated requirements (MKT-V01..06) are reused, not re-planned.

---

## Phase Details

### Phase 1: Backend Boot + Streaming Hello-World
**Goal:** Open `http://localhost:8000` in a browser; see one ticker (AAPL) streaming a live price that updates ~2× per second. Achieved via `docker build && docker run` (no scripts yet).
**Mode:** mvp
**Requirements:** APP-01, APP-02, APP-03, APP-04, APP-05, APP-06, FE-01, FE-02, FE-03, FE-04, FE-06, PKG-01, PKG-03
**Success Criteria:**
1. `docker build` succeeds from a clean checkout; `docker run -p 8000:8000 finally` starts the container.
2. `curl http://localhost:8000/api/health` returns `200 OK` with a JSON status payload.
3. `curl http://localhost:8000/api/stream/prices` returns an `text/event-stream` connection that yields a `data:` event within 2 seconds.
4. Opening `http://localhost:8000/` in a browser shows a single ticker (AAPL) with a live-updating price and a green/red flash effect on each tick.
5. Stopping the container and starting it again restarts cleanly; the SimulatorDataSource lifecycle runs without errors in the container logs.

### Phase 2: Watchlist Display
**Goal:** The full 10-ticker default watchlist is visible in the UI with live prices, daily change %, and a sparkline that fills in over time. SQLite is created on first request and seeded with the defaults.
**Mode:** mvp
**Requirements:** DB-01, DB-02, DB-03, DB-04, DB-09, WL-01, FE-07
**Success Criteria:**
1. First request to the running app creates `db/finally.db` with `users_profile` (1 row, $10k cash) and `watchlist` (10 rows for AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX) seeded.
2. `GET /api/watchlist` returns the 10 tickers with their latest prices hydrated from `PriceCache`.
3. The frontend renders a watchlist grid: 10 rows, each with ticker, live price (flashing on update), and daily % change.
4. A sparkline beside each ticker fills in client-side as SSE events arrive (visible drawing after ~10 seconds).
5. Container restart preserves the database (named volume).

### Phase 3: Trading
**Goal:** User can buy and sell from a trade bar at the top of the page; cash, positions, and portfolio total update immediately. The positions table shows current holdings with unrealized P&L.
**Mode:** mvp
**Requirements:** DB-05, DB-06, PORT-01, PORT-02, PORT-03, PORT-04, FE-05, FE-11, FE-12
**Success Criteria:**
1. Header shows live portfolio total (cash + position market values) updating as prices stream.
2. `POST /api/portfolio/trade {ticker, quantity, side}` debits/credits cash, updates the positions row, appends a `trades` row, and returns the updated portfolio.
3. Validation errors (insufficient cash, insufficient shares, unknown ticker, non-positive quantity) return a JSON error with a human message and the trade bar surfaces it inline.
4. Buying a fractional quantity (e.g., 1.5 shares) works end-to-end; the position's `quantity` and `avg_cost` math is correct after multiple buys at different prices.
5. Positions table renders one row per held position with ticker / qty / avg cost / current price / unrealized P&L / % change, updating live.

### Phase 4: Portfolio Visuals
**Goal:** Two visualizations make the portfolio shape and history visible at a glance — a treemap heatmap of positions (sized by weight, colored by P&L) and a line chart of total portfolio value over time.
**Mode:** mvp
**Requirements:** DB-07, PORT-05, PORT-06, FE-09, FE-10
**Success Criteria:**
1. A background task writes a `portfolio_snapshots` row every 30 seconds and on every trade execution.
2. `GET /api/portfolio/history` returns snapshot rows in newest-first order with an optional `limit` query param.
3. Portfolio heatmap renders one rectangle per held position, sized by current portfolio weight, colored on a red↔green scale by % P&L.
4. P&L line chart renders `total_value` over time using the history endpoint; new snapshots appear in the chart as time passes.
5. With an empty portfolio (no positions), both visualizations render an empty-state message instead of erroring.

### Phase 5: Watchlist Management
**Goal:** User can add and remove tickers from the watchlist via the UI; the running market-data source picks up the change without a restart.
**Mode:** mvp
**Requirements:** WL-02, WL-03, WL-04, FE-14
**Success Criteria:**
1. `POST /api/watchlist {ticker}` normalizes the ticker (upper, trim), inserts into the table, calls `source.add_ticker(ticker)`, and returns the new row hydrated with the latest price.
2. `DELETE /api/watchlist/{ticker}` removes the row, calls `source.remove_ticker(ticker)`, and removes the ticker from `PriceCache`.
3. Duplicate add or invalid ticker format returns a JSON validation error.
4. Watchlist UI exposes an add-ticker input and a per-row remove control; both invoke the API and the grid updates without a page reload.
5. Newly added tickers begin streaming prices within one SSE cadence interval (~500 ms simulator; ~15 s Massive).

### Phase 6: AI Chat — Read-Only
**Goal:** User can converse with the LLM about their portfolio in a docked chat panel. The agent has full portfolio + watchlist + price context. Conversation persists across page reloads. No auto-execute yet.
**Mode:** mvp
**Requirements:** DB-08, CHAT-01, CHAT-02 (parsed but `trades`/`watchlist_changes` ignored this phase), CHAT-06, CHAT-07, FE-13 (render conversation + loading state, no action chips)
**Success Criteria:**
1. `POST /api/chat {message}` assembles context (system prompt, portfolio snapshot, recent `chat_messages` history, user message), calls LiteLLM → OpenRouter → `openrouter/openai/gpt-oss-120b` via the Cerebras provider with structured outputs per `.claude/skills/cerebras/SKILL.md`, returns the parsed `{message, ...}` JSON.
2. User and assistant messages are persisted to `chat_messages`; reloading the page restores the conversation.
3. `LLM_MOCK=true` swaps the LLM call for a deterministic mock that returns canned structured responses matched by message content.
4. Chat panel renders the conversation history, accepts new messages, and shows a loading indicator while waiting for the LLM.
5. Any `trades` / `watchlist_changes` in the structured response are parsed (schema-valid) but explicitly **not** executed — they're logged for the next phase to wire up.

### Phase 7: AI Chat — Auto-Execute
**Goal:** The agentic centerpiece. The LLM's structured response auto-executes any included trades and watchlist changes via the same validation as manual actions. Failures are surfaced to the user and back to the agent's next turn. Each action shows as a confirmation chip in the assistant's message.
**Mode:** mvp
**Requirements:** CHAT-03, CHAT-04, CHAT-05, FE-13 (action chips)
**Success Criteria:**
1. A chat message like "Buy 10 shares of NVDA" results in a real trade execution; portfolio total, positions table, and cash all update without further user action.
2. Validation failures (e.g., "Sell 1000 shares of TSLA" when the user holds none) do not crash the chat — the failure is captured, attached to the assistant message, and included in the next turn's LLM context so the agent can apologize/explain.
3. Watchlist additions and removals from chat (e.g., "Add PYPL to the watchlist") execute and the watchlist grid updates live.
4. The chat panel renders each executed action as an inline chip below the assistant message ("✓ Bought 10 NVDA @ $801.23", "✓ Added PYPL"). Failed actions show with a red "✗" and the validation message.
5. Mock-mode (`LLM_MOCK=true`) returns canned responses that include `trades`/`watchlist_changes` so the auto-execute path is exercised by E2E.

### Phase 8: Sentiment Badges
**Goal:** Each ticker in the watchlist shows a small colored badge (bullish / neutral / bearish) reflecting an LLM-inferred sentiment. Score is cached server-side and refreshed periodically.
**Mode:** mvp
**Requirements:** SENT-01, SENT-02, SENT-03, SENT-04, FE-07 (badge slot)
**Success Criteria:**
1. `GET /api/sentiment/{ticker}` returns `{ticker, score: "bullish"|"neutral"|"bearish", summary, generated_at}` from an LLM call; subsequent calls within the TTL (default 5 min) return the cached value.
2. `GET /api/watchlist` includes the per-ticker sentiment inline; tickers not yet scored return `"unknown"` and trigger a background refresh.
3. Watchlist UI renders the badge beside each ticker, color-coded (green / gray / red) with a tooltip showing the summary on hover.
4. `LLM_MOCK=true` returns deterministic per-ticker mock sentiment values for E2E tests.
5. Removing a ticker from the watchlist evicts its sentiment cache entry.

### Phase 9: Selected Ticker Chart
**Goal:** Clicking a ticker in the watchlist promotes it to a main chart area showing a larger price-over-time visualization.
**Mode:** mvp
**Requirements:** FE-08
**Success Criteria:**
1. Clicking a ticker row in the watchlist updates a "selected ticker" piece of UI state.
2. The main chart area renders a price-over-time chart for the selected ticker, fed by accumulated SSE samples since page load (canvas-based — Lightweight Charts or Recharts).
3. Switching the selected ticker swaps the chart's data set without a page reload.
4. The chart shows clear axis labels, the current price, and the % change since the chart's first data point.
5. With no ticker selected (initial state), the area shows a "select a ticker" empty state.

### Phase 10: Packaging Polish
**Goal:** Start/stop scripts on macOS, Linux, and Windows. `.env.example` committed. Optional docker-compose convenience wrapper. New contributor can clone and run in under five minutes.
**Mode:** mvp
**Requirements:** PKG-02, PKG-04, PKG-05, PKG-06
**Success Criteria:**
1. `scripts/start_mac.sh` builds the image if missing, runs the container with the named volume and `--env-file .env`, prints the URL, and is idempotent (safe to run twice).
2. `scripts/stop_mac.sh` stops and removes the container without removing the named volume.
3. `scripts/start_windows.ps1` and `scripts/stop_windows.ps1` provide PowerShell equivalents with the same idempotency.
4. `.env.example` lists every required and optional env var (`OPENROUTER_API_KEY`, `MASSIVE_API_KEY`, `LLM_MOCK`) with short comments.
5. `docker-compose.yml` exists as a one-service convenience wrapper around the same image and volume.

### Phase 11: E2E Testing
**Goal:** Playwright suite catches regressions in the demo flows. Runs in CI-friendly mode with `LLM_MOCK=true`.
**Mode:** mvp
**Requirements:** TEST-03, TEST-04
**Success Criteria:**
1. `test/docker-compose.test.yml` brings up the app container with `LLM_MOCK=true` and a Playwright container that runs against it.
2. Test scenario: fresh-start — default watchlist of 10 tickers appears, $10k cash, prices stream for at least 3 seconds.
3. Test scenario: add and remove a ticker — UI reflects both within 2 seconds; data source picks up the new ticker.
4. Test scenario: buy and sell — cash decreases on buy, position appears, sell increases cash and removes the position.
5. Test scenario: AI chat — sending a "buy 5 NVDA" message via the chat results in a position appearing and the action chip rendering inline.

### Phase 12: Docs & Reconciliation
**Goal:** Project docs reflect what actually shipped, not what `PLAN.md` originally aspired to. Stale references removed.
**Mode:** mvp
**Requirements:** DOC-01, DOC-02, DOC-03
**Success Criteria:**
1. Root `CLAUDE.md` is regenerated by GSD's `generate-claude-md` so it no longer `@`-references the deleted `planning/PLAN.md` and instead points at `.planning/` artifacts.
2. Root `README.md` directory layout matches the actual repo (`frontend/`, `backend/`, `db/`, `test/`, `scripts/`, `.planning/`); quick-start instructions work end-to-end on a clean machine.
3. `backend/CLAUDE.md` is updated: either the `market_data_demo.py` deletion lands and the doc reference is removed, or the demo is restored and the doc reference still works.
4. `.env.example` instructions in the README match the variables that actually exist (PKG-02 already shipped them).
5. `git status` is clean — no stranded "pending delete" entries from the GSD reset.

---

## Notes

- **Phase 0 (implicit):** The market-data subsystem (`backend/app/market/`) is treated as already-shipped infrastructure. Phase 1 consumes it (via `create_market_data_source` and `create_stream_router`) but does not modify it.
- **Working-tree hazard:** `backend/pyproject.toml` is staged for deletion in the working tree at the time this roadmap was written. Phase 1's first plan must restore it (`git restore backend/pyproject.toml`) or the rest of the phase is dead in the water. This is captured in APP-06.
- **Per-phase test discipline:** Every phase's Definition of Done includes (a) unit tests for new backend modules, (b) unit tests for new frontend components, and (c) any new code passes `ruff check`. Phase 11 adds the E2E layer on top of (not in place of) per-phase units.
- **No research subagent ran.** The roadmap was authored inline from PROJECT.md + REQUIREMENTS.md + the codebase map. If a phase later needs domain research, `/gsd:plan-phase N` can spawn the researcher at that point (provided agents are installed by then).
