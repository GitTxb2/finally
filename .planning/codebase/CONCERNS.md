---
last_mapped_commit:
---

# Concerns

**Mapped:** 2026-05-17

## Summary

The market-data slice itself is clean — small, well-tested, internally consistent. The real concerns are around it: the working tree is mid-reorganization (`pyproject.toml`, `planning/`, and the demo are staged for deletion), there's no application entrypoint wiring the slice to FastAPI, the SSE route is uncovered by tests, and the broader product (portfolio, AI chat, frontend, persistence, Docker) is documented but unimplemented. Triage these before the next GSD phase starts execution.

## Working-Tree Hazards (must resolve before any new work)

### 🚨 `backend/pyproject.toml` is pending deletion

- `git status` shows `D backend/pyproject.toml`. The file is the project manifest — without it, `uv sync` fails and the test suite cannot run.
- It's still present at HEAD (`38b3398`). Either restore it (`git restore backend/pyproject.toml`) or decide that the GSD plan-phase will re-create it as part of a "scaffold backend" step. **Do not commit the deletion as-is.**

### 🚨 `planning/PLAN.md` is pending deletion but `CLAUDE.md` still references it

- Root `CLAUDE.md` line ~5: `@planning/PLAN.md`. The file is staged for deletion, so the very next session will fail to load that reference.
- The spec content itself is still recoverable from commit `38b3398` (`git show 38b3398:planning/PLAN.md`) — preserve it under `.planning/PROJECT.md` (per GSD convention) before letting the deletion land, or update `CLAUDE.md` to point at the new location.

### ⚠ Other staged deletions to triage

- `backend/market_data_demo.py` — Rich terminal demo. Referenced by `backend/CLAUDE.md:59` (`uv run market_data_demo.py`). If the demo is gone, the doc lies. Pick one: restore the demo, or update `backend/CLAUDE.md`.
- `planning/MARKET_DATA_SUMMARY.md`, `planning/REVIEW.md`, `planning/archive/*` — old GSD-adjacent docs. Recover their content into `.planning/` history first if anything is irreplaceable, otherwise the deletion is fine.

## Architecture / Wiring Gaps

### No FastAPI application root

- `create_stream_router(price_cache)` returns a router, but **nothing constructs a `FastAPI()` app and mounts it.** No `backend/app/main.py`. The system has no production entrypoint — only tests exercise the real wiring.
- Knock-on effect: nothing instantiates the singleton `PriceCache`, calls `await create_market_data_source(cache).start([...])` on app startup, or `stop()` on shutdown. A future "boot the backend" phase needs to add this and decide where the cache lifecycle lives (most likely a FastAPI `lifespan` async context manager).

### SSE route is untested

- `backend/app/market/stream.py` has zero tests. The disconnect-detection path (`request.is_disconnected()`), the `retry: 1000` initial chunk, and the version-change suppression in `_generate_events` are all unverified.
- Risk: a regression in the stream loop (e.g., an early `return` swallowing the `retry` hint, or `await sleep` outside the loop body) wouldn't be caught.
- Suggested fix: add `httpx.AsyncClient(transport=ASGITransport(app=...))` SSE tests, or at minimum unit-test `_generate_events` as an async generator with a fake `request`.

### Massive client polls a fixed `tickers` snapshot

- `MassiveDataSource.add_ticker` / `remove_ticker` mutate `self._tickers`, and the next call to `_fetch_snapshots` picks up the new list (`massive_client.py:123`). But `_poll_loop` only sleeps then polls — there's no "poll now" signal on `add_ticker`, so a newly added ticker takes up to `poll_interval` (default 15 s) seconds to first appear in the cache. Symmetric for `remove_ticker`, which calls `cache.remove(ticker)` immediately but leaves stale data possible if a poll was already in flight.
- This is acceptable for the current single-user demo cadence, but worth knowing before the watchlist UI is wired up.

## Tech Debt — Smaller Stuff

- **No `.env.example`**, despite `README.md:30` instructing users to `cp .env.example .env`. The file is missing; new contributors will hit a cryptic "No such file" before they realise the README is aspirational.
- **No type-checker.** Ruff covers style and naming, but there's no `mypy`/`pyright` config. `numpy` types in particular (`np.ndarray | None`, `self._cholesky @ z_independent`) would benefit from static checking before the codebase grows.
- **`backend/app/__init__.py` is empty (one docstring line).** Fine for now, but if the app gets a `main.py` it might be worth promoting common imports / a `get_app()` factory.
- **`from massive import RESTClient`** at module top of `massive_client.py:8` — if the `massive` package fails to import (e.g., transient install issue), the whole backend fails to import, even when `MASSIVE_API_KEY` is unset and the user only wants the simulator. Commit `6a2b36e` deliberately removed the lazy import. This is the right call for prod, but be aware: any change that breaks `massive` blocks even simulator-only smoke tests.
- **`numpy>=2.0.0`** — a hard pin to NumPy 2.x. Fine, but Python ecosystem support is still catching up; if a dependency conflict surfaces, the pin is where to look.
- **GBM math uses a stdlib `random` for events and `np.random.standard_normal` for diffusion.** Both paths are unseeded → simulator output is non-reproducible across test runs. Tests don't depend on specific prices, so this hasn't bitten anything, but if anyone tries to write a "golden price" test it will fail. Consider a seedable `numpy.random.Generator` if reproducibility ever matters.

## Security Notes

- **Single-user assumption is hard-coded.** Everywhere the spec calls for a `user_id`, the column defaults to `"default"`. There's no auth in the codebase, no rate limiting on the SSE endpoint, no CORS config. All of this is *intentional* for the demo, but explicitly noting it so it doesn't accidentally ship to a public URL.
- **No input validation on tickers.** `add_ticker` only does `.upper().strip()` (Massive) — a future watchlist endpoint will need to reject non-symbol input before it reaches the simulator/Massive call.
- **The `.env` file (55 bytes) exists at the project root.** Gitignored correctly, but worth a `gitleaks`-style check before any public push.

## Documentation Drift

- Root `CLAUDE.md` references `planning/PLAN.md` and `planning/MARKET_DATA_SUMMARY.md` — both pending deletion.
- `README.md` describes a `frontend/`, `db/`, `test/`, `scripts/` layout that doesn't exist.
- `backend/CLAUDE.md` references `market_data_demo.py` — pending deletion.

These are mostly aspirational docs from the original PLAN that haven't been pruned to reflect actual code. Easy to fix during `/gsd:new-project`'s PROJECT.md synthesis — make sure the new docs distinguish "shipped" from "planned."

## CI Gaps

- No workflow runs `pytest` or `ruff`. The two `claude-code-*.yml` workflows orchestrate the Claude bot but don't gate merges on tests. Tests pass today; nothing automated prevents tomorrow's regression.
