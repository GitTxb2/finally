---
last_mapped_commit:
---

# Integrations

**Mapped:** 2026-05-17

## Summary

One outbound integration is wired: the **Massive (Polygon.io) REST API** for real market data, gated by `MASSIVE_API_KEY`. All other integrations from `PLAN.md` (OpenRouter LLM, SQLite persistence, OAuth, etc.) are documented but not yet implemented.

## Outbound

### Massive (Polygon.io) REST API

- **Client:** `backend/app/market/massive_client.py:8` (`from massive import RESTClient`, `from massive.rest.models import SnapshotMarketType`).
- **Endpoint used:** `client.get_snapshot_all(market_type=SnapshotMarketType.STOCKS, tickers=self._tickers)` — single call returns snapshots for all watched tickers (see `_fetch_snapshots` at `backend/app/market/massive_client.py:123`).
- **Auth:** `api_key` constructor arg, sourced from `MASSIVE_API_KEY` env var via `create_market_data_source()` (`backend/app/market/factory.py:24`).
- **Polling cadence:** `poll_interval` constructor arg, defaults to `15.0` seconds (free-tier safe — 5 req/min). Loop in `_poll_loop` (`backend/app/market/massive_client.py:83`).
- **Concurrency model:** The Massive SDK is synchronous; the client wraps `_fetch_snapshots()` in `asyncio.to_thread(...)` (`backend/app/market/massive_client.py:97`) so the event loop is not blocked.
- **Data shape consumed:** `snap.ticker`, `snap.last_trade.price`, `snap.last_trade.timestamp` (Unix milliseconds → divided by `1000.0` to seconds at `backend/app/market/massive_client.py:103`).
- **Error handling:** Single broad `except Exception` (`backend/app/market/massive_client.py:118`) — logged at `error` level, swallowed so the loop survives. Per-snapshot `AttributeError`/`TypeError` caught individually at `backend/app/market/massive_client.py:110` and skipped with a warning.
- **Retry / backoff:** None. Just waits the next `poll_interval`. 401, 429, network errors are all collapsed into the same warn-and-continue path.

### Inbound / Selected

- **Built-in simulator (`SimulatorDataSource`, `backend/app/market/simulator.py:200`)** — the no-key default. Geometric Brownian Motion with Cholesky-correlated draws (`numpy.linalg.cholesky`). Runs as an in-process `asyncio.Task` (`name="simulator-loop"`), updates the shared `PriceCache` every 500 ms by default.
- Selection logic: `backend/app/market/factory.py:16` — `MASSIVE_API_KEY` set & non-empty → Massive; else simulator.

## Inbound (HTTP)

### SSE Stream

- **Endpoint:** `GET /api/stream/prices` declared at `backend/app/market/stream.py:26` via `APIRouter(prefix="/api/stream", tags=["streaming"])`.
- **Construction:** `create_stream_router(price_cache)` factory at `backend/app/market/stream.py:20` — caller passes in a `PriceCache` instance.
- **Response:** `StreamingResponse` with `media_type="text/event-stream"`, headers `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no` (to defeat nginx buffering).
- **Reconnection hint:** First chunk yields `retry: 1000\n\n` so browsers' native `EventSource` retries after 1 s on drop (`backend/app/market/stream.py:62`).
- **Cadence:** Polls `price_cache.version` every `interval` (default `0.5`s) — only emits when the version changes, so SSE clients see roughly one event per simulator/Massive tick.
- **Disconnect detection:** `await request.is_disconnected()` inside the generator loop (`backend/app/market/stream.py:71`).
- **Not mounted:** No FastAPI `app = FastAPI()` exists. The router is constructed only inside tests and a (now-deleted) demo script. There is no live HTTP entrypoint yet.

## Planned but Not Implemented

| Integration | Where documented | Status |
|-------------|------------------|--------|
| OpenRouter / Cerebras LLM | `README.md:23`, `.claude/skills/cerebras/SKILL.md` | Not in code |
| SQLite (`db/finally.db`) | `README.md:55-57`, `PLAN.md` (deleted) | Not in code |
| OAuth / auth providers | `PLAN.md` (deleted) — explicitly out of scope for v1 | Not in code |
| Webhooks | None | — |

## Secrets Handling

- `.env` exists at the project root (gitignored).
- `.env.example` is **not** in the repo (referenced by `README.md:30` but missing).
- No secrets-management library (e.g., `python-dotenv`, `pydantic-settings`) is wired up — the only env-var read in code is `os.environ.get("MASSIVE_API_KEY", "")` at `backend/app/market/factory.py:24`.
