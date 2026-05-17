---
last_mapped_commit:
---

# Architecture

**Mapped:** 2026-05-17

## Summary

A small, vertically sliced subsystem: **producer (data source) → in-memory cache → SSE consumer**. The producer is selected at construction time by a factory based on `MASSIVE_API_KEY`. There is no application composition root yet — the pieces are wired together only by tests and (until recently) a demo script. The slice is intentionally decoupled: cache readers (SSE, future portfolio code) never call the data source.

## Layering

```
┌────────────────────────────────────────────────────────────────┐
│  HTTP layer (FastAPI)                                          │
│    backend/app/market/stream.py                                │
│    create_stream_router(price_cache) → APIRouter               │
│    GET /api/stream/prices  ── reads ──▶ PriceCache             │
└────────────────────────────────────────────────────────────────┘
                          ▲ reads from
                          │
┌────────────────────────────────────────────────────────────────┐
│  Shared state (in-memory, thread-safe)                         │
│    backend/app/market/cache.py                                 │
│    PriceCache  ──── monotonic version counter ────             │
└────────────────────────────────────────────────────────────────┘
                          ▲ writes to
                          │
┌────────────────────────────────────────────────────────────────┐
│  Data sources (MarketDataSource interface)                     │
│    backend/app/market/interface.py    ─ abstract base          │
│    backend/app/market/simulator.py    ─ SimulatorDataSource    │
│    backend/app/market/massive_client.py ─ MassiveDataSource    │
│         ▲                                                       │
│         │ chosen by                                             │
│    backend/app/market/factory.py:create_market_data_source     │
│         ▲                                                       │
│         │ depends on                                            │
│    MASSIVE_API_KEY env var                                     │
└────────────────────────────────────────────────────────────────┘
```

## Pattern: Producer–Cache–Consumer

- **Decoupling contract:** No code outside `backend/app/market/` should call data sources directly. Read the cache. This is so that SSE/portfolio/trade execution stay agnostic of simulator-vs-real, and so the system trivially scales to multiple consumers.
- **Producer lifecycle** (`backend/app/market/interface.py:8`):
  - `await source.start(tickers)` — spawns an `asyncio.Task` writing into the cache.
  - `await source.add_ticker(t)` / `await source.remove_ticker(t)` — mutate the active set.
  - `await source.stop()` — cancels the task, idempotent.
- **Cache as the source of truth** (`backend/app/market/cache.py:11`):
  - `dict[ticker, PriceUpdate]` guarded by a `threading.Lock`.
  - **Monotonic `_version`** counter bumped on every `update()` — the SSE generator uses this to skip emitting when nothing changed (`backend/app/market/stream.py:75-77`). This is the only synchronization between producer and consumer; there are no async events / queues.

## Key Abstractions

### `MarketDataSource` (ABC) — `backend/app/market/interface.py:8`

Defines the producer contract. Two concrete implementations:

| Implementation | Driver | Cadence | Thread model |
|----------------|--------|---------|---------------|
| `SimulatorDataSource` (`simulator.py:200`) | `GBMSimulator.step()` in `_run_loop` | `update_interval=0.5s` default | Pure async — math is in-process |
| `MassiveDataSource` (`massive_client.py:17`) | `RESTClient.get_snapshot_all` in `_poll_loop` | `poll_interval=15.0s` default | Sync SDK wrapped with `asyncio.to_thread` |

### `GBMSimulator` — `backend/app/market/simulator.py:28`

Pure math object (no I/O). Geometric Brownian Motion with sector-correlated shocks via Cholesky decomposition of a correlation matrix rebuilt on every add/remove. Per-ticker `mu`/`sigma` and seed prices live in `backend/app/market/seed_prices.py`. Tiny `dt` (~8.48e-8, a 500 ms slice of a 252-day × 6.5 h trading year) keeps per-tick moves sub-cent. Random "events" (~0.1 % per tick) shock price 2-5 %.

### `PriceUpdate` — `backend/app/market/models.py:10`

Frozen `@dataclass(frozen=True, slots=True)`. Computed properties (`change`, `change_percent`, `direction`) and `to_dict()` for SSE/JSON serialization. Immutability is enforced by tests (`backend/tests/market/test_models.py:73`).

### `PriceCache` — `backend/app/market/cache.py:11`

Thread-safe (`threading.Lock`, not `asyncio.Lock`) because the only writer that ever touches it from a non-asyncio thread is `MassiveDataSource._fetch_snapshots` via `asyncio.to_thread`. All reads/writes go through the lock; `get_all()` returns a shallow copy. Prices are rounded to 2 decimals on insert.

## Entry Points

- **No production entrypoint.** No `main.py`, no `app = FastAPI()`, no `uvicorn` command line in `pyproject.toml`.
- **Test entrypoint:** `cd backend && uv run pytest`. All real wiring (cache → source → cache → SSE generator) happens inside tests in `backend/tests/market/`.
- **Demo (deleted in working tree):** `backend/market_data_demo.py` — Rich-based terminal dashboard. Still referenced by `backend/CLAUDE.md:59` and listed under git HEAD; the deletion is pending commit.

## Data Flow Example — SSE Request

1. (Setup, before any request) — somewhere, code calls `cache = PriceCache(); source = create_market_data_source(cache); await source.start(["AAPL", ...])`. Today this only happens in tests.
2. `SimulatorDataSource._run_loop` (or `MassiveDataSource._poll_loop`) writes new prices into `cache` every 500 ms / 15 s, bumping `cache._version`.
3. Browser opens `GET /api/stream/prices`. `stream_prices` returns a `StreamingResponse` wrapping `_generate_events(price_cache, request)`.
4. `_generate_events` yields `retry: 1000\n\n`, then enters its loop. Each iteration:
   - Checks `await request.is_disconnected()` — bails if true.
   - Compares `price_cache.version` to `last_version`; if changed, snapshots `get_all()` and yields `data: {<ticker>: <update.to_dict()>, ...}\n\n`.
   - `await asyncio.sleep(0.5)`.
5. Browser's `EventSource` parses and dispatches events; on TCP drop, auto-reconnects after the `retry: 1000` hint.

## What's Missing vs `PLAN.md`

`PLAN.md` (deleted from working tree, restorable from commit `38b3398`) describes a much larger system: SQLite, portfolio + trades + chat tables, REST endpoints for `/api/portfolio/*`, `/api/watchlist/*`, `/api/chat`, an OpenRouter-driven LLM agent, Next.js frontend, Docker, Playwright. **None of that exists in code.** Only the market-data slice has been built.
