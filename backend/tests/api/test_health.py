"""Tests for the ``/api/health`` endpoint."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from app.main import create_app


@pytest.fixture(autouse=True)
def _no_massive_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure factory selects SimulatorDataSource."""
    monkeypatch.delenv("MASSIVE_API_KEY", raising=False)


async def test_health_returns_expected_payload_shape() -> None:
    """``/api/health`` returns 200 with the agreed JSON shape after lifespan startup."""
    app = create_app()
    async with app.router.lifespan_context(app):
        # Wait one simulator tick so the cache populates.
        await asyncio.sleep(0.6)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"status", "source", "tickers", "cache_version"}
    assert body["status"] == "ok"
    assert body["tickers"] == 10
    assert isinstance(body["cache_version"], int)
    assert body["cache_version"] >= 1


async def test_health_source_label_is_simulator_without_api_key() -> None:
    """With no ``MASSIVE_API_KEY``, the factory returns SimulatorDataSource → label "simulator"."""
    app = create_app()
    async with app.router.lifespan_context(app):
        await asyncio.sleep(0.6)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["source"] == "simulator"
