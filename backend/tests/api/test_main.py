"""Tests for app.main — the FastAPI factory and core routes."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_sse_route_is_mounted(client: TestClient) -> None:
    """The /api/stream/prices endpoint must be registered on the app."""
    routes = {(getattr(r, "path", None), tuple(getattr(r, "methods", ()) or ())) for r in client.app.routes}
    assert any(path == "/api/stream/prices" and "GET" in methods for path, methods in routes)


def test_static_index_served_at_root(client: TestClient) -> None:
    """With the placeholder static dir in place, GET / returns index.html."""
    response = client.get("/")
    assert response.status_code == 200
    assert "FinAlly" in response.text


def test_api_routes_take_precedence_over_static(client: TestClient) -> None:
    """Static mount at / must not shadow /api/* routes."""
    api_response = client.get("/api/health")
    assert api_response.status_code == 200
    assert api_response.json() == {"status": "ok"}


def test_price_cache_populated_after_startup(client: TestClient) -> None:
    """The lifespan handler should seed the cache with the default watchlist."""
    app = client.app
    cache = app.state.price_cache
    # SimulatorDataSource seeds prices into the cache on start(), before the
    # async loop kicks in, so they're present as soon as lifespan completes.
    assert len(cache) > 0
    # All ten default watchlist tickers should be tracked.
    tickers = set(cache.get_all().keys())
    expected = {"AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "NFLX"}
    assert expected.issubset(tickers)
