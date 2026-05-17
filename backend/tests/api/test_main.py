"""Tests for ``app.main`` — app factory and lifespan wiring."""

from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI

from app.main import create_app
from app.market import PriceCache
from app.market.seed_prices import SEED_PRICES


@pytest.fixture(autouse=True)
def _no_massive_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MASSIVE_API_KEY", raising=False)


def test_create_app_returns_fastapi_instance() -> None:
    """``create_app()`` returns a FastAPI instance with ``/api/health`` routed."""
    app = create_app()
    assert isinstance(app, FastAPI)
    assert app.title == "FinAlly"
    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/api/health" in paths


async def test_lifespan_starts_and_stops_source() -> None:
    """Lifespan populates ``app.state`` and stops the source cleanly on exit."""
    app = create_app()
    async with app.router.lifespan_context(app):
        assert isinstance(app.state.price_cache, PriceCache)
        assert app.state.market_source is not None
        # One simulator tick (~0.5s default) — wait a hair longer for safety.
        await asyncio.sleep(0.6)
        assert len(app.state.price_cache.get_all()) == 10

    # After context exit, the source's background task has been awaited to None.
    assert app.state.market_source._task is None


async def test_lifespan_uses_seed_prices_default_tickers() -> None:
    """Lifespan seeds the source with ``list(SEED_PRICES.keys())``."""
    app = create_app()
    async with app.router.lifespan_context(app):
        await asyncio.sleep(0.6)
        cache_keys = set(app.state.price_cache.get_all().keys())

    assert set(SEED_PRICES.keys()).issubset(cache_keys)
