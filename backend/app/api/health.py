"""``GET /api/health`` endpoint.

Reports the application's runtime state for Docker HEALTHCHECK and curl smoke
tests. Reads singleton state from ``request.app.state`` — no module-level
references to the cache or source.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)

router = APIRouter()


_SOURCE_LABELS = {
    "SimulatorDataSource": "simulator",
    "MassiveDataSource": "massive",
}


def _source_label(source: Any) -> str:
    """Map a ``MarketDataSource`` subclass to a short label."""
    name = type(source).__name__
    if name in _SOURCE_LABELS:
        return _SOURCE_LABELS[name]
    # Fallback: e.g. "FakeDataSource" -> "fake"
    return name.lower().removesuffix("datasource") or name.lower()


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    """Return application status, market-source label, ticker count, cache version."""
    cache = request.app.state.price_cache
    source = request.app.state.market_source
    return {
        "status": "ok",
        "source": _source_label(source),
        "tickers": len(cache.get_all()),
        "cache_version": cache.version,
    }
