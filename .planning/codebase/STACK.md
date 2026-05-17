---
last_mapped_commit:
---

# Stack

**Mapped:** 2026-05-17

## Summary

Python 3.12 backend, single module (`backend/app/market`) implementing a streaming market-data subsystem. FastAPI + SSE for the wire protocol, NumPy for correlated GBM simulation, optional Polygon.io ("Massive") client for real data. Managed as a `uv` project. No frontend, database, or HTTP entrypoint yet — only the market-data slice has been built.

## Languages & Runtime

| Language | Version | Where |
|----------|---------|-------|
| Python   | `>=3.12` (pinned via `requires-python` in `backend/pyproject.toml`) | `backend/app/`, `backend/tests/` |

No TypeScript / Node code in tree yet (planned for `frontend/`).

## Package Management

- **Tool:** `uv` (Astral) — fast Python project manager.
- **Manifest:** `backend/pyproject.toml` (PEP 621 + Hatchling build backend).
- **Lockfile:** `backend/uv.lock` (813 lines, committed).
- **Virtual env:** `backend/.venv/` (gitignored).
- **Install:** `cd backend && uv sync --extra dev`.

> ⚠ `backend/pyproject.toml` is currently marked **deleted** in the working tree (per `git status`) but still present at HEAD (`38b3398`). The file is needed to install/test the backend; document references below assume the HEAD version.

## Runtime Dependencies

From `backend/pyproject.toml` (HEAD):

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

**None present.** `PLAN.md` (pre-deletion) called for Next.js (TypeScript, static export, Tailwind) served as static files by FastAPI, but no `frontend/` directory exists in HEAD or working tree.

## Database

**None present.** `PLAN.md` called for SQLite with lazy init at `db/finally.db`; no schema, ORM, or migration code in repo. `db/` directory does not exist.

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

`.env` exists at the project root (55 bytes, gitignored).

## Notable Absences

- No `Dockerfile`, no `docker-compose.yml` — `README.md` documents `docker build -t finally .` but neither file is in the repo.
- No `scripts/start_*.sh` / `start_windows.ps1` referenced by `PLAN.md`.
- No `test/` directory for Playwright E2E.
- No FastAPI app entrypoint (`app = FastAPI()`) — `create_stream_router()` returns a router, but nothing mounts it.
