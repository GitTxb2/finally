"""FastAPI application entrypoint. See SKELETON.md for architectural decisions."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import api_router
from app.market import PriceCache, create_market_data_source, create_stream_router
from app.market.seed_prices import SEED_PRICES

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Construct the cache + market source, mount the SSE router, run the source.

    Order matters:
    1. Cache + source are constructed FIRST so the SSE router (which takes the
       cache by argument) and ``app.state`` consumers see real objects.
    2. ``create_stream_router(cache)`` is mounted before ``source.start()`` so
       any SSE connection made during the brief startup gap still gets the
       cache-version watcher.
    3. ``source.stop()`` runs in ``finally`` to honor the idempotent stop()
       contract under any shutdown path.
    """
    cache = PriceCache()
    source = create_market_data_source(cache)
    default_tickers = list(SEED_PRICES.keys())

    app.include_router(create_stream_router(cache))
    app.state.price_cache = cache
    app.state.market_source = source

    await source.start(default_tickers)
    logger.info(
        "FinAlly backend started with %d tickers via %s",
        len(default_tickers),
        type(source).__name__,
    )
    try:
        yield
    finally:
        await source.stop()
        logger.info("FinAlly backend stopped cleanly")


def create_app() -> FastAPI:
    """Build the FastAPI app with lifespan, API router, and (later) static mount.

    Returned as a factory so tests can construct isolated app instances.
    """
    app = FastAPI(title="FinAlly", lifespan=lifespan)
    app.include_router(api_router, prefix="/api")
    # Static-files mount for the Next.js export is added in Plan 01-03.
    return app


app = create_app()
