---
last_mapped_commit:
---

# Conventions

**Mapped:** 2026-05-17

## Summary

The backend codebase is small, recent, and consistent. Modern Python (3.12+) with `from __future__ import annotations` at the top of every source file, frozen dataclasses for value objects, abstract base classes for interfaces, and factory functions for env-driven selection. Logging via the stdlib `logging` module (no `print`). Ruff enforces import order and basic correctness.

## Lint / Format

From `backend/pyproject.toml` (HEAD):

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]
```

- **E** (pycodestyle errors), **F** (Pyflakes), **I** (isort), **N** (pep8-naming), **W** (warnings). No type checker (mypy/pyright) configured.
- Line length 100. `E501` ignored — format handles wrapping.
- Imports sorted by Ruff's isort rule. Stdlib → third-party → local, blank-line separated.

## Type Hints

- **PEP 604 unions everywhere** — `PriceUpdate | None`, `dict[str, PriceUpdate]`, `list[str]`. No `Optional[...]`, no `Union[...]`.
- `from __future__ import annotations` at the top of every module so all hints are lazy strings (no runtime import cost, supports forward refs).
- Return types are annotated on every public method; private helpers also annotated where the type aids comprehension (`_pairwise_correlation(t1: str, t2: str) -> float`).
- `np.ndarray | None` for the Cholesky matrix (`backend/app/market/simulator.py:65`).
- No `Protocol` use — interfaces are `ABC` with `@abstractmethod`.

## Class Design

- **Value objects:** `@dataclass(frozen=True, slots=True)` — see `PriceUpdate` (`backend/app/market/models.py:9`). Immutability enforced by tests.
- **Services / stateful objects:** plain classes with `_` -prefixed private state and explicit `__init__` (no dataclasses). See `PriceCache`, `GBMSimulator`, `SimulatorDataSource`, `MassiveDataSource`.
- **Interfaces:** `ABC` + `@abstractmethod` — see `MarketDataSource` (`backend/app/market/interface.py:8`). Implementations inherit and do not call `super().__init__()` (the ABC has no `__init__`).
- **Lifecycle methods are async:** `start`, `stop`, `add_ticker`, `remove_ticker` — even when no I/O is awaited (kept async for interface consistency).
- **`stop()` is always idempotent** — see `SimulatorDataSource.stop` (`simulator.py:232`), `MassiveDataSource.stop` (`massive_client.py:55`). Both null out `_task` after cancelling so a double `stop()` is a no-op. Covered by `test_stop_is_idempotent` / `test_stop_is_clean`.

## Concurrency

- **`threading.Lock` for shared state** — `PriceCache` uses `threading.Lock` (not `asyncio.Lock`) because `MassiveDataSource` writes from a worker thread via `asyncio.to_thread` (`massive_client.py:97`). Every method that touches `_prices` or `_version` is inside a `with self._lock:` block.
- **Named asyncio tasks** — `asyncio.create_task(self._run_loop(), name="simulator-loop")` (`simulator.py:229`) and `name="massive-poller"` (`massive_client.py:48`). Named tasks make debugging easier.
- **Cancellation pattern** — `stop()` does `task.cancel()` then `await task` inside `try/except CancelledError: pass`. Don't swallow other exceptions in this pattern.
- **Loop resilience** — `SimulatorDataSource._run_loop` (`simulator.py:260`) wraps each iteration's body in `try/except Exception: logger.exception(...)` so a single bad step doesn't kill the producer.

## Logging

- **Module-level logger:** every module that logs starts with `logger = logging.getLogger(__name__)`.
- **Levels:**
  - `logger.info(...)` — lifecycle events ("Simulator started with %d tickers", "SSE client connected: %s").
  - `logger.debug(...)` — high-volume events (Massive poll updates, random simulator events).
  - `logger.warning(...)` — per-snapshot failures inside Massive (recoverable).
  - `logger.error(...)` — Massive poll failure (caught, loop continues).
  - `logger.exception(...)` — used in the simulator loop only (`simulator.py:269`) to capture stack traces.
- **No `print()` anywhere** in `app/`.
- **Lazy `%s` formatting** — `logger.info("Massive: added ticker %s", ticker)`, never f-strings inside logger calls.

## Error Handling

- **Narrow `except` clauses** at API/data boundaries: `AttributeError, TypeError` when parsing a Massive snapshot (`massive_client.py:110`).
- **Broad `except Exception`** only inside the poll/step loops where the goal is "survive and try again next tick" — paired with logging and no re-raise (`massive_client.py:118`, `simulator.py:268`).
- **No custom exception classes.** No `raise CustomError(...)` anywhere.
- **No retries / backoff.** The poll loop just waits the next interval.
- **Graceful no-ops** on edge cases: `PriceCache.remove(ticker)` uses `dict.pop(ticker, None)`; `add_ticker` checks "already present" first; `remove_ticker` no-ops when absent.

## Docstrings

- **Triple-quoted, one-line summary at minimum** on every module, class, and public method.
- **Multi-paragraph docstrings** on non-trivial methods include: behavior, lifecycle/invariants, and rationale (see `MarketDataSource.start` at `interface.py:25` and `GBMSimulator.step` at `simulator.py:74`).
- **Math comments** in `GBMSimulator` explain the GBM formula and the `dt` derivation (`simulator.py:32-48`).
- **No docstring on tests.** Each test method has a short docstring; that's it.

## Imports

- Always: `from __future__ import annotations` first.
- Then stdlib, third-party, local — separated by blank lines.
- **No `import *`.** Public API surface is curated explicitly in `backend/app/market/__init__.py`.
- Module-level imports only (no lazy/conditional imports — commit `6a2b36e` explicitly removed them: *"Remove lazy imports for massive package"*).

## Constants

- **UPPER_SNAKE_CASE** at module scope for tuning knobs and tables: `SEED_PRICES`, `TICKER_PARAMS`, `CORRELATION_GROUPS`, `INTRA_TECH_CORR`, `TSLA_CORR` (`seed_prices.py`); `TRADING_SECONDS_PER_YEAR`, `DEFAULT_DT` as class attributes on `GBMSimulator` (`simulator.py:47`).
- Magic numbers explained with comments — see `simulator.py:46-48` for the `dt` derivation.

## Rounding

- All prices stored to 2 decimals (`cache.py:36-38`, `simulator.py:116`).
- `change` and `change_percent` rounded to 4 decimals (`models.py:21`, `models.py:28`).
- Tests verify both invariants (`test_price_rounding`, `test_prices_rounded_to_two_decimals`).
