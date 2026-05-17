---
last_mapped_commit:
---

# Testing

**Mapped:** 2026-05-17

## Summary

`pytest` + `pytest-asyncio` (auto-mode) + `pytest-cov` for the backend. 6 test modules, ~70 tests, all under `backend/tests/market/`. One test file per source module. Real concurrency is exercised at short intervals; external I/O (Massive REST) is mocked. No frontend or E2E tests yet.

## Stack

| Tool | Version | Purpose |
|------|---------|---------|
| `pytest` | `>=8.3.0` | Runner |
| `pytest-asyncio` | `>=0.24.0` | Async support, `asyncio_mode = "auto"` |
| `pytest-cov` | `>=5.0.0` | Coverage (`uv run pytest --cov=app --cov-report=html`) |

Pinned in `backend/pyproject.toml` under `[project.optional-dependencies].dev` (file is pending delete in working tree but present at HEAD).

## Configuration

From `backend/pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"

[tool.coverage.run]
source = ["app"]
omit = ["tests/*"]
```

`asyncio_mode = "auto"` means *every* `async def test_*` is auto-collected — no `@pytest.mark.asyncio` needed (though some test classes use `@pytest.mark.asyncio` at class level anyway, e.g. `backend/tests/market/test_simulator_source.py:11`).

## Fixtures (`backend/tests/conftest.py`)

Minimal — one fixture only:

```python
@pytest.fixture
def event_loop_policy():
    """Use the default event loop policy for all async tests."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
```

No factory fixtures, no DB fixtures, no test data builders. Each test constructs its own `PriceCache()` and source. This keeps tests easy to read in isolation.

## Test Organization

Mirrors source. One `test_<module>.py` per source module (except `seed_prices.py`, which is pure constants):

| Test module | Style | Notes |
|-------------|-------|-------|
| `test_models.py` | Sync unit | Pure `PriceUpdate` math + immutability check |
| `test_cache.py` | Sync unit | Direct `PriceCache` API exercise |
| `test_factory.py` | Sync unit | `unittest.mock.patch.dict(os.environ, ...)` for env-var branching |
| `test_simulator.py` | Sync unit | Tests `GBMSimulator` (pure math, no async). Includes a 10k-step positivity stress test. |
| `test_simulator_source.py` | Async integration | `@pytest.mark.asyncio` class. Drives the real loop with `update_interval=0.05–0.1`, sleeps, asserts version increments. |
| `test_massive.py` | Async unit | `@pytest.mark.asyncio` class. All `_fetch_snapshots` calls patched with `unittest.mock`. |

Naming convention: `TestClassName` suite, `test_<behavior>_<expected_outcome>` method (`test_direction_up`, `test_api_error_does_not_crash`, `test_add_ticker_uppercase_normalization`).

## Mocking Strategy

- **External SDK calls are mocked.** `MassiveDataSource._fetch_snapshots` is monkey-patched in every Massive test using `patch.object(source, "_fetch_snapshots", return_value=[...])`. The Massive `RESTClient` is patched with `patch("app.market.massive_client.RESTClient")` when `start()` is exercised.
- **Mock snapshots are built with a helper** — `_make_snapshot(ticker, price, timestamp_ms)` in `backend/tests/market/test_massive.py:11`.
- **Env vars** are isolated with `patch.dict(os.environ, {...}, clear=True)` (`test_factory.py`).
- **The simulator is not mocked.** Tests exercise real GBM math, real `numpy`, real `asyncio.Task`. Short intervals (50–100 ms) and `asyncio.sleep` keep wall time low.
- **`PriceCache` is never mocked.** It's the integration surface — tests build a real cache and assert on its state.

## Coverage

- `coverage source = ["app"]` so coverage tracks production code only.
- Excluded report lines: `pragma: no cover`, `def __repr__`, `raise AssertionError`, `raise NotImplementedError`, `if __name__ == .__main__.:`, `if TYPE_CHECKING:`.
- Run with `uv run --extra dev pytest --cov=app --cov-report=html` per `backend/CLAUDE.md:51`.

## Running Tests

```bash
cd backend
uv sync --extra dev           # install once
uv run pytest -v              # all tests, verbose
uv run pytest --cov=app       # with coverage
uv run pytest tests/market/test_simulator.py   # one file
```

## CI

**No CI runs tests today.** The two GitHub Actions workflows in `.github/workflows/` are Claude-Code orchestration (`@claude` bot and PR code review) — neither installs `uv`, runs `pytest`, or enforces `ruff`. Adding a CI job is on the table for any future GSD phase that touches the backend.

## Not Yet Tested

- `backend/app/market/stream.py` — `create_stream_router` and `_generate_events` have **no** test coverage. The SSE generator's disconnect handling, retry hint, and version-change suppression are not exercised. (Would require a `fastapi.testclient` or `httpx.AsyncClient` test.)
- Frontend, E2E, and `LLM_MOCK` mode — none of the related code exists yet.
