# FinAlly Project - the Finance Ally

All project documentation is in the `planning` directory.

The key document is PLAN.md included in full below; the market data component has been completed and is summarized in the file `planning/MARKET_DATA_SUMMARY.md` with more details in the `planning/archive` folder. Consult these docs only when required. The remainder of the platform is still to be developed.

@planning/PLAN.md

<!-- GSD:project-start source:PROJECT.md -->
## Project

**FinAlly — AI Trading Workstation**

A single-Docker simulated trading workstation built as a capstone for an agentic-AI coding course. It streams live ticker prices into a Bloomberg-style dark UI; the user trades a simulated $10,000 portfolio with market orders; and an AI chat assistant — with full auto-execute authority — analyzes positions, manages the watchlist, and places trades on the user's behalf. Per-ticker sentiment badges (LLM-generated) sit beside each ticker as an at-a-glance signal.

**Core Value:** Demonstrates orchestrated AI coding agents producing a polished, demo-quality agentic-AI app — the AI chat agent's ability to take real action (trade, modify watchlist) without confirmation is the centerpiece of the story.

### Constraints

- **Tech stack — Backend**: FastAPI on Python ≥3.12, managed by `uv` — Already chosen and partly built. Switching now wastes the market-data implementation and the test suite.
- **Tech stack — Frontend**: Next.js with TypeScript, built via `output: 'export'` static export, served as static files by FastAPI — Single-origin deployment, no CORS, one port, one container.
- **Tech stack — Persistence**: SQLite at `db/finally.db`, lazy-initialized — No auth means no multi-user means no need for a database server.
- **Tech stack — Real-time**: Server-Sent Events (SSE), not WebSockets — One-way push is all we need; simpler protocol, universal browser support, already implemented.
- **Tech stack — LLM**: LiteLLM → OpenRouter → `openrouter/openai/gpt-oss-120b` via the Cerebras provider, using structured outputs — Defined by the course's `.claude/skills/cerebras/SKILL.md` skill.
- **Deployment**: Single Docker container, exposed on port 8000, with a named volume for the SQLite file — Students run one command (no `docker-compose` for production, no service orchestration).
- **UX — Aesthetic**: Dark Bloomberg-terminal look. Accent yellow `#ecad0a`, primary blue `#209dd7`, submit-button purple `#753991`. Backgrounds around `#0d1117`/`#1a1a2e`. Price flash animations on tick (green/red, ~500 ms fade).
- **UX — Layout**: Desktop-first, dense, multi-pane; responsive but not mobile-optimized.
- **Demo timeline**: Course capstone deadline (date TBD by user) — coarse-grained phases over many fine-grained ones.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Summary
## Languages & Runtime
| Language | Version | Where |
|----------|---------|-------|
| Python   | `>=3.12` (pinned via `requires-python` in `backend/pyproject.toml`) | `backend/app/`, `backend/tests/` |
## Package Management
- **Tool:** `uv` (Astral) — fast Python project manager.
- **Manifest:** `backend/pyproject.toml` (PEP 621 + Hatchling build backend).
- **Lockfile:** `backend/uv.lock` (813 lines, committed).
- **Virtual env:** `backend/.venv/` (gitignored).
- **Install:** `cd backend && uv sync --extra dev`.
## Runtime Dependencies
| Package | Pin | Purpose |
|---------|-----|---------|
| `fastapi` | `>=0.115.0` | HTTP / SSE framework (`backend/app/market/stream.py`) |
| `uvicorn[standard]` | `>=0.32.0` | ASGI server (not wired to an `app` entrypoint yet) |
| `numpy` | `>=2.0.0` | Cholesky decomposition + standard-normal draws in `simulator.py` |
| `massive` | `>=1.0.0` | Polygon.io REST client used by `MassiveDataSource` |
| `rich` | `>=13.0.0` | Terminal styling for `backend/market_data_demo.py` (also deleted in working tree) |
## Dev Dependencies (`[project.optional-dependencies].dev`)
| Package | Pin | Purpose |
|---------|-----|---------|
| `pytest` | `>=8.3.0` | Test runner |
| `pytest-asyncio` | `>=0.24.0` | Async test support (`asyncio_mode = "auto"`) |
| `pytest-cov` | `>=5.0.0` | Coverage reporting (`uv run pytest --cov=app`) |
| `ruff` | `>=0.7.0` | Lint + format (`line-length = 100`, `target-version = "py312"`) |
## Tooling Configuration (from `backend/pyproject.toml`)
- **Ruff:** lint rules `E, F, I, N, W`; `E501` (line length) ignored — formatter handles it.
- **Pytest:** `testpaths = ["tests"]`, `asyncio_mode = "auto"`, `asyncio_default_fixture_loop_scope = "function"`.
- **Coverage:** `source = ["app"]`, omits tests; excludes `__repr__`, `TYPE_CHECKING`, etc.
- **Build:** Hatchling, packages = `["app"]` (wheel built from `backend/app/`).
## Frontend Stack
## Database
## CI / Tooling Outside Backend
- `.github/workflows/claude.yml` — Triggers `anthropics/claude-code-action@v1` on `@claude` mentions in issues/PR comments.
- `.github/workflows/claude-code-review.yml` — Runs `code-review@claude-code-plugins` on every PR (`opened, synchronize, ready_for_review, reopened`).
- No traditional test/lint CI workflow yet — backend tests are not run automatically.
## Environment Variables
| Variable | Status | Effect |
|----------|--------|--------|
| `MASSIVE_API_KEY` | Optional | When non-empty → `MassiveDataSource` (real polling); otherwise → `SimulatorDataSource` (GBM). Read in `backend/app/market/factory.py:24`. |
| `OPENROUTER_API_KEY` | Documented in `README.md` for the AI chat feature (not yet implemented). | — |
| `LLM_MOCK` | Documented for E2E mock mode (not yet implemented). | — |
## Notable Absences
- No `Dockerfile`, no `docker-compose.yml` — `README.md` documents `docker build -t finally .` but neither file is in the repo.
- No `scripts/start_*.sh` / `start_windows.ps1` referenced by `PLAN.md`.
- No `test/` directory for Playwright E2E.
- No FastAPI app entrypoint (`app = FastAPI()`) — `create_stream_router()` returns a router, but nothing mounts it.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Summary
## Lint / Format
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
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Summary
## Layering
```
```
## Pattern: Producer–Cache–Consumer
- **Decoupling contract:** No code outside `backend/app/market/` should call data sources directly. Read the cache. This is so that SSE/portfolio/trade execution stay agnostic of simulator-vs-real, and so the system trivially scales to multiple consumers.
- **Producer lifecycle** (`backend/app/market/interface.py:8`):
- **Cache as the source of truth** (`backend/app/market/cache.py:11`):
## Key Abstractions
### `MarketDataSource` (ABC) — `backend/app/market/interface.py:8`
| Implementation | Driver | Cadence | Thread model |
|----------------|--------|---------|---------------|
| `SimulatorDataSource` (`simulator.py:200`) | `GBMSimulator.step()` in `_run_loop` | `update_interval=0.5s` default | Pure async — math is in-process |
| `MassiveDataSource` (`massive_client.py:17`) | `RESTClient.get_snapshot_all` in `_poll_loop` | `poll_interval=15.0s` default | Sync SDK wrapped with `asyncio.to_thread` |
### `GBMSimulator` — `backend/app/market/simulator.py:28`
### `PriceUpdate` — `backend/app/market/models.py:10`
### `PriceCache` — `backend/app/market/cache.py:11`
## Entry Points
- **No production entrypoint.** No `main.py`, no `app = FastAPI()`, no `uvicorn` command line in `pyproject.toml`.
- **Test entrypoint:** `cd backend && uv run pytest`. All real wiring (cache → source → cache → SSE generator) happens inside tests in `backend/tests/market/`.
- **Demo (deleted in working tree):** `backend/market_data_demo.py` — Rich-based terminal dashboard. Still referenced by `backend/CLAUDE.md:59` and listed under git HEAD; the deletion is pending commit.
## Data Flow Example — SSE Request
## What's Missing vs `PLAN.md`
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

| Skill | Description | Path |
|-------|-------------|------|
| cerebras-inference | Use this to write code to call an LLM using LiteLLM and OpenRouter with the Cerebras inference provider | `.claude/skills/cerebras/SKILL.md` |
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
