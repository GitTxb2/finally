# FinAlly — End-to-End Tests

Playwright E2E suite. Runs against the production Docker image with `LLM_MOCK=true`.

## Running

From the project root:

```bash
docker compose -f test/docker-compose.test.yml build
docker compose -f test/docker-compose.test.yml run --rm playwright
docker compose -f test/docker-compose.test.yml down -v
```

For local iteration (when the app is already running at http://localhost:8000):

```bash
cd test
npm ci
BASE_URL=http://localhost:8000 npx playwright test
```

## Required `data-testid` selectors

The specs target stable selectors so they survive copy/style changes. The
frontend must expose the following hooks (FE-2, FE-3, FE-4):

### Layout / Header
- `data-testid="app-shell"` — top-level layout root (any visible container is fine)
- `data-testid="cash-balance"` — element whose text contains the cash USD value
- `data-testid="connection-status"` — element with `data-state="connected|reconnecting|disconnected"` (any of: `connected|live|open`, `reconnect|retry|disconnect|offline` is accepted; pick one)

### Main chart
- `data-testid="main-chart"` — chart container; exposes `data-ticker="{TICKER}"` (or `"none"` when nothing is selected). The `<svg>` is stable; the path `d` attribute updates on tick. Use `data-ticker` for selection assertions — it's synchronous and survives the "AWAITING TAPE…" placeholder when a newly-selected ticker has <2 ticks.

### Watchlist
- `data-testid="watchlist-row-{TICKER}"` — one per ticker (e.g. `watchlist-row-AAPL`); also exposes `data-selected="true|false"` for the currently selected ticker (selection drives the main chart)
- `data-testid="watchlist-price-{TICKER}"` — current price cell, with `data-direction="up|down|flat"` reflecting the last tick
- `data-testid="watchlist-add-input"` — input for adding a new ticker
- `data-testid="watchlist-add-button"` — submit button for add
- `data-testid="watchlist-remove-{TICKER}"` — per-row remove button (hover-revealed; hover the row first or use `.click({ force: true })`)

### Trade bar
- `data-testid="trade-ticker-input"`
- `data-testid="trade-quantity-input"`
- `data-testid="trade-buy-button"` — form submit; Enter on the quantity input also submits a Buy
- `data-testid="trade-sell-button"` — `type="button"`, not a form submit
- `data-testid="trade-error-toast"` — appears when a trade fails validation (insufficient cash, unknown ticker, etc.)
- `data-testid="toast-success"`, `data-testid="toast-info"` — bonus testids

### Portfolio views
- `data-testid="position-row-{TICKER}"` — `<tr>`-level testid; text includes ticker, quantity (trailing zeros stripped), avg cost, last, P&L $, P&L %. Clicking selects the ticker into the main chart.
- `data-testid="heatmap-tile-{TICKER}"` — one tile per held position; sized by `market_value`, tinted by P&L %. Excluded when `market_value` is null.
- `data-testid="pnl-chart"` — P&L chart container; sub-elements are inline `<svg><path>` plus a `<circle>` for the last point — `pnl-chart >> svg path` matches.

> Portfolio components live on the bottom row and may be below the fold. Specs use `locator.scrollIntoViewIfNeeded()` before asserting visibility.

### Chat
- `data-testid="chat-toggle"` — bottom-right toggle button
- `data-testid="chat-panel"` — always in the DOM; use `data-open="true|false"` to detect state (panel is translated off-screen when closed, not unmounted)
- `data-testid="chat-input"`, `data-testid="chat-send"`
- `data-testid="chat-message-user"`, `data-testid="chat-message-assistant"` — one per bubble
- `data-testid="chat-typing"` — present only while a request is in flight
- `data-testid="chat-action-trade"` — chip per executed trade; text format `BUY 5 AAPL @ $190.50` (or `SELL`)
- `data-testid="chat-action-watchlist"` — chip per watchlist mutation; text format `WATCH + PYPL`, `WATCH − GOOGL`, `ALREADY WATCHED X`, `NOT WATCHED X`

Behavior to be aware of:
- Successful chat responses with trades or watchlist changes auto-refetch `/api/portfolio` + `/api/portfolio/history`.
- Watchlist refresh comes from the SSE stream picking up the new ticker (no hard refetch from chat).
- Server 502 (LLM error per BE-4 contract) renders an error banner above the input and an assistant error bubble.

## Mock LLM trigger phrases

`LLM_MOCK=true` is set on the container. The chat backend (`backend/app/llm/mock.py`)
matches these patterns case-insensitively, first-match-wins, with "remove"
checked before "add". No real LLM call is made.

| Trigger phrase | Result |
|---|---|
| `buy <N> <TICKER>` | `trades: [{ticker, side: "buy", quantity: N}]` (N may be decimal) |
| `sell <N> <TICKER>` | `trades: [{ticker, side: "sell", quantity: N}]` |
| `add <TICKER>` / `watch <TICKER>` | `watchlist_changes: [{ticker, action: "add"}]` |
| `remove <TICKER>` / `unwatch <TICKER>` | `watchlist_changes: [{ticker, action: "remove"}]` |
| message containing `error` or `fail` | backend raises `LLMError` (test error path) |
| anything else | `message: "[mock] Portfolio summary: cash=... total=... positions=..."`, empty actions |

Caveats:
- Tickers must be 1-5 letters (no digits/symbols).
- Mixing "add X and remove Y" yields ONLY the remove. Use separate messages.

## Scenarios covered

| Spec file | Scenario |
|---|---|
| `01-fresh-start.spec.ts` | 10 default tickers, $10,000 cash, prices stream within 5s |
| `02-watchlist.spec.ts` | Add/remove a watchlist ticker via UI |
| `03-buy-sell.spec.ts` | Buy decreases cash and creates a position; sell reverses it |
| `04-portfolio-views.spec.ts` | Heatmap tile visible, P&L chart has a data point |
| `05-ai-chat.spec.ts` | Mock chat: trade and watchlist auto-execution chips, fallback path |
| `06-sse-resilience.spec.ts` | Connection indicator reflects reconnect cycle |
| `07-price-flash.spec.ts` | Watchlist price cell emits up/down direction on tick |
| `08-main-chart.spec.ts` | Watchlist row click updates main-chart `data-ticker` |
