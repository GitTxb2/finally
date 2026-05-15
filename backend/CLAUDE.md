# Backend — Developer Guide

## Project Setup

```bash
cd backend
uv sync --extra dev   # Install all dependencies including test/lint tools
```

## Market Data API

The market data subsystem lives in `app/market/`. Use these imports:

```python
from app.market import PriceCache, PriceUpdate, MarketDataSource, create_market_data_source
```

### Core Types

- **`PriceUpdate`** — Immutable dataclass: `ticker`, `price`, `previous_price`, `timestamp`, plus properties `change`, `change_percent`, `direction` ("up"/"down"/"flat"), and `to_dict()` for JSON serialization.

- **`PriceCache`** — Thread-safe in-memory store. Key methods:
  - `update(ticker, price, timestamp=None) -> PriceUpdate`
  - `get(ticker) -> PriceUpdate | None`
  - `get_price(ticker) -> float | None`
  - `get_all() -> dict[str, PriceUpdate]`
  - `remove(ticker)`
  - `version` property — monotonic counter, increments on every update (for SSE change detection)

- **`MarketDataSource`** — Abstract interface implemented by `SimulatorDataSource` and `MassiveDataSource`. Lifecycle: `start(tickers)` -> `add_ticker()` / `remove_ticker()` -> `stop()`.

- **`create_market_data_source(cache)`** — Factory. Returns `MassiveDataSource` if `MASSIVE_API_KEY` is set, otherwise `SimulatorDataSource`.

### SSE Streaming

```python
from app.market import create_stream_router

router = create_stream_router(price_cache)  # Returns FastAPI APIRouter
# Endpoint: GET /api/stream/prices (text/event-stream)
```

### Seed Data

Default tickers: AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX. Seed prices and per-ticker volatility/drift params are in `app/market/seed_prices.py`.

## LLM API

The LLM subsystem lives in `app/llm/`. Use these imports:

```python
from app.llm import chat, ChatResponse, Trade, WatchlistChange, Msg, LLMError
```

### Entry point

```python
chat(
    system_prompt: str | None = None,        # None -> default FinAlly prompt
    history: list[Msg] | None = None,        # prior turns in chronological order
    portfolio_context: dict | None = None,   # rendered as a system message
    user_message: str = "",                  # required, non-empty
) -> ChatResponse
```

`ChatResponse` shape (Pydantic):
- `message: str` — conversational reply
- `trades: list[Trade]` — each `{ticker, side: "buy"|"sell", quantity: float>0}`
- `watchlist_changes: list[WatchlistChange]` — each `{ticker, action: "add"|"remove"}`

Raises `LLMError` on empty `user_message`, missing `OPENROUTER_API_KEY` (live mode), transport failures, or malformed responses.

Backed by LiteLLM -> OpenRouter with model `openrouter/openai/gpt-oss-120b` and `extra_body={"provider": {"order": ["cerebras"]}}`. Structured outputs via `response_format=ChatResponse`.

### Mock mode

When `LLM_MOCK=true`, `chat()` returns deterministic responses without any network call (and without needing `OPENROUTER_API_KEY`). Trigger phrases (case-insensitive, first match wins):

| Phrase pattern        | Result                                              |
|-----------------------|-----------------------------------------------------|
| `buy <N> <TICKER>`    | one buy trade for N shares of TICKER                |
| `sell <N> <TICKER>`   | one sell trade for N shares of TICKER               |
| `remove <TICKER>` / `unwatch <TICKER>` | watchlist remove                       |
| `add <TICKER>` / `watch <TICKER>`      | watchlist add                          |
| contains `error` or `fail` | raises `LLMError` (for error-path tests)       |
| anything else         | brief portfolio summary from `portfolio_context`    |

Tickers are 1-5 letters and are returned uppercased.

## Running Tests

```bash
uv run --extra dev pytest -v              # All tests
uv run --extra dev pytest --cov=app       # With coverage
uv run --extra dev ruff check app/ tests/ # Lint
```

## Demo

```bash
uv run market_data_demo.py   # Live terminal dashboard with simulated prices
```

