---
last_mapped_commit:
---

# Structure

**Mapped:** 2026-05-17

## Top-Level Layout

```
finally/
├── backend/                ← uv project (Python 3.12)
│   ├── app/
│   │   ├── __init__.py            (1 line, docstring only)
│   │   └── market/                ← only implemented subsystem
│   │       ├── __init__.py        (public API surface)
│   │       ├── interface.py       (MarketDataSource ABC)
│   │       ├── models.py          (PriceUpdate dataclass)
│   │       ├── cache.py           (PriceCache, thread-safe)
│   │       ├── factory.py         (create_market_data_source)
│   │       ├── simulator.py       (GBMSimulator + SimulatorDataSource)
│   │       ├── massive_client.py  (MassiveDataSource)
│   │       ├── seed_prices.py     (default tickers + GBM params)
│   │       └── stream.py          (SSE router factory)
│   ├── tests/
│   │   ├── conftest.py
│   │   └── market/
│   │       ├── test_models.py
│   │       ├── test_cache.py
│   │       ├── test_factory.py
│   │       ├── test_simulator.py
│   │       ├── test_simulator_source.py
│   │       └── test_massive.py
│   ├── pyproject.toml             ⚠ pending delete in working tree (at HEAD)
│   ├── uv.lock                    (813 lines, committed)
│   ├── README.md
│   └── CLAUDE.md                  (developer guide for the market module)
├── .github/workflows/
│   ├── claude.yml                 (@claude bot)
│   └── claude-code-review.yml     (PR code-review action)
├── .claude/                        (Claude Code / GSD config — not source)
│   └── skills/cerebras/SKILL.md   (LiteLLM + OpenRouter snippet)
├── README.md                       (product-level overview)
├── CLAUDE.md                       (project instructions, references planning/PLAN.md)
├── LICENSE
└── .gitignore                      (Python defaults — .venv, .env, .ruff_cache, etc.)
```

## Working-Tree Deletions (pending commit)

Per `git status` on branch `gsd-finally`:

| Path | Status | Note |
|------|--------|------|
| `backend/pyproject.toml` | `D` (deleted) | Needed for `uv sync`; almost certainly going to be restored |
| `backend/market_data_demo.py` | `D` | Rich terminal demo; referenced by `backend/CLAUDE.md:59` |
| `planning/PLAN.md` | `D` | The product spec; referenced by root `CLAUDE.md` |
| `planning/MARKET_DATA_SUMMARY.md` | `D` | |
| `planning/REVIEW.md` | `D` | |
| `planning/archive/MARKET_DATA_DESIGN.md` | `D` | |
| `planning/archive/MARKET_DATA_REVIEW.md` | `D` | |
| `planning/archive/MARKET_INTERFACE.md` | `D` | |
| `planning/archive/MARKET_SIMULATOR.md` | `D` | |
| `planning/archive/MASSIVE_API.md` | `D` | |

The wipe is consistent with switching planning over to `.planning/` (GSD).

## Module Layout (`backend/app/market/`)

One folder, one concern. Each module is small (`<300` lines) and has a single responsibility:

| File | Purpose | Public symbols |
|------|---------|----------------|
| `__init__.py` | Re-exports the public API and documents it in the module docstring | `PriceUpdate`, `PriceCache`, `MarketDataSource`, `create_market_data_source`, `create_stream_router` |
| `models.py` | `PriceUpdate` immutable dataclass + derived properties | `PriceUpdate` |
| `cache.py` | `PriceCache` with `threading.Lock` and monotonic version counter | `PriceCache` |
| `interface.py` | Abstract `MarketDataSource` contract | `MarketDataSource` |
| `simulator.py` | `GBMSimulator` (pure math) + `SimulatorDataSource` (async wrapper) | `GBMSimulator`, `SimulatorDataSource` |
| `massive_client.py` | `MassiveDataSource` (Polygon REST polling, thread-offloaded) | `MassiveDataSource` |
| `factory.py` | Env-driven selection between sim and Massive | `create_market_data_source` |
| `seed_prices.py` | Constants: seed prices, per-ticker `mu`/`sigma`, correlation groups | `SEED_PRICES`, `TICKER_PARAMS`, `DEFAULT_PARAMS`, `CORRELATION_GROUPS`, `INTRA_TECH_CORR`, `INTRA_FINANCE_CORR`, `CROSS_GROUP_CORR`, `TSLA_CORR` |
| `stream.py` | FastAPI router factory + SSE generator | `create_stream_router` |

## Test Layout (`backend/tests/`)

Mirrors `app/`. `tests/market/` contains one test module per source module (except `seed_prices.py`, which is constants-only):

| Test file | Tests for | Style |
|-----------|-----------|-------|
| `test_models.py` | `models.py` | Sync unit tests |
| `test_cache.py` | `cache.py` | Sync unit tests |
| `test_factory.py` | `factory.py` | Sync with `patch.dict(os.environ, ...)` |
| `test_simulator.py` | `simulator.py:GBMSimulator` | Sync; one stress test runs 10k steps |
| `test_simulator_source.py` | `simulator.py:SimulatorDataSource` | `@pytest.mark.asyncio` integration tests with short intervals |
| `test_massive.py` | `massive_client.py` | `@pytest.mark.asyncio`; all I/O mocked via `patch.object(source, "_fetch_snapshots", ...)` |

`conftest.py` defines an `event_loop_policy` fixture returning `asyncio.DefaultEventLoopPolicy()`.

## Key Locations Cheat Sheet

- **Add a new ticker default:** `backend/app/market/seed_prices.py` (`SEED_PRICES`, `TICKER_PARAMS`).
- **Change correlation behavior:** `seed_prices.py` constants + `GBMSimulator._pairwise_correlation` (`simulator.py:174`).
- **Change SSE cadence:** `_generate_events` default `interval=0.5` at `stream.py:54`.
- **Change Massive poll interval:** `MassiveDataSource.__init__` default `poll_interval=15.0` at `massive_client.py:32`.
- **Change simulator tick rate:** `SimulatorDataSource.__init__` default `update_interval=0.5` at `simulator.py:210`.
- **Add a new data source:** implement `MarketDataSource` (`interface.py:8`), then branch in `factory.py:create_market_data_source`.

## Naming Conventions

- Files: `snake_case.py`.
- Classes: `PascalCase` — `PriceUpdate`, `PriceCache`, `GBMSimulator`, `SimulatorDataSource`, `MassiveDataSource`, `MarketDataSource`.
- Tests: `Test<ClassName>` suites, `test_<behavior>_<expectation>` methods (`test_direction_up`, `test_api_error_does_not_crash`).
- Private attributes prefixed `_` — `_cache`, `_tickers`, `_task`, `_cholesky`, `_version`.
- Factories named `create_<thing>` (`create_market_data_source`, `create_stream_router`).
