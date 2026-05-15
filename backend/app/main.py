"""FinAlly FastAPI application entrypoint.

Wires together:
  - The market data subsystem (PriceCache + data source + SSE router)
  - REST routers (added by BE-2, BE-3, BE-4 as they land)
  - Static file serving for the Next.js export
  - Lazy SQLite initialization (via the first `connect()` call on startup)
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import chat as chat_routes
from app.api import portfolio as portfolio_routes
from app.api import watchlist as watchlist_routes
from app.db import record_snapshot
from app.db.connection import connect
from app.market import PriceCache, create_market_data_source, create_stream_router

logger = logging.getLogger(__name__)

STATIC_DIR_ENV = "STATIC_DIR"
DEFAULT_STATIC_DIR = "static"
SNAPSHOT_INTERVAL_SECONDS = 30.0


def _resolve_static_dir() -> Path:
    """Resolve the directory holding the built frontend (Next.js export)."""
    raw = os.environ.get(STATIC_DIR_ENV, DEFAULT_STATIC_DIR)
    return Path(raw)


def _read_initial_watchlist() -> list[str]:
    """Read the seeded watchlist tickers from SQLite.

    The first `connect()` call lazily creates the schema and seeds the
    default watchlist, so this works on a fresh database too.
    """
    with connect() as conn:
        rows = conn.execute(
            "SELECT ticker FROM watchlist WHERE user_id = 'default' ORDER BY added_at"
        ).fetchall()
    return [row["ticker"] for row in rows]


async def _snapshot_loop(price_cache: PriceCache, interval: float) -> None:
    """Record a portfolio snapshot every `interval` seconds.

    The lifespan handler launches this as a background task so the P&L chart
    has a steady stream of data points. Each tick computes the current portfolio
    value (cash + sum of position market values) and writes a row to
    portfolio_snapshots.
    """
    from app.api.portfolio import compute_portfolio

    while True:
        try:
            await asyncio.sleep(interval)
            snapshot = compute_portfolio(price_cache)
            record_snapshot(snapshot.total_value)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Snapshot loop iteration failed")


def create_app() -> FastAPI:
    """Application factory.

    Returns a configured FastAPI app. Wrapped in a factory so tests can
    construct fresh instances pointing at temp SQLite paths.
    """
    price_cache = PriceCache()
    market_source = create_market_data_source(price_cache)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        tickers = _read_initial_watchlist()
        await market_source.start(tickers)
        logger.info("Market data source started with %d tickers", len(tickers))

        snapshot_task = asyncio.create_task(
            _snapshot_loop(price_cache, SNAPSHOT_INTERVAL_SECONDS),
            name="portfolio-snapshot-loop",
        )
        try:
            yield
        finally:
            snapshot_task.cancel()
            try:
                await snapshot_task
            except asyncio.CancelledError:
                pass
            await market_source.stop()
            logger.info("Market data source stopped")

    app = FastAPI(title="FinAlly", lifespan=lifespan)

    # Expose the shared instances on app.state so REST routers can reach them.
    app.state.price_cache = price_cache
    app.state.market_source = market_source

    @app.get("/api/health")
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    app.include_router(create_stream_router(price_cache))
    app.include_router(watchlist_routes.router)
    app.include_router(portfolio_routes.router)
    app.include_router(chat_routes.router)

    # Static file mount must come LAST so /api/* routes win.
    static_dir = _resolve_static_dir()
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
    else:
        logger.warning(
            "Static directory %s does not exist; frontend will not be served. "
            "Set %s or build the frontend.",
            static_dir,
            STATIC_DIR_ENV,
        )

    return app


app = create_app()
