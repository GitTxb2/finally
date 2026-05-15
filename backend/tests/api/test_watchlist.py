"""Tests for the /api/watchlist REST endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.db import watchlist as watchlist_repo


def test_get_watchlist_returns_default_seed(client: TestClient) -> None:
    response = client.get("/api/watchlist")
    assert response.status_code == 200
    body = response.json()
    tickers = [entry["ticker"] for entry in body]
    expected = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "NFLX"]
    assert set(tickers) == set(expected)
    # Every entry has at least a ticker field; cached entries also have a price.
    for entry in body:
        assert "ticker" in entry
        if entry.get("price") is not None:
            assert "previous_price" in entry
            assert "direction" in entry


def test_post_watchlist_adds_new_ticker(client: TestClient) -> None:
    response = client.post("/api/watchlist", json={"ticker": "PYPL"})
    assert response.status_code == 201
    assert response.json() == {"ticker": "PYPL", "status": "added"}
    assert "PYPL" in watchlist_repo.list_tickers()
    # And the market source now tracks it (price seeded).
    cache = client.app.state.price_cache
    assert cache.get("PYPL") is not None


def test_post_watchlist_normalizes_case_and_whitespace(client: TestClient) -> None:
    response = client.post("/api/watchlist", json={"ticker": "  amd  "})
    assert response.status_code == 201
    assert response.json()["ticker"] == "AMD"
    assert "AMD" in watchlist_repo.list_tickers()


def test_post_watchlist_duplicate_is_idempotent(client: TestClient) -> None:
    first = client.post("/api/watchlist", json={"ticker": "AMD"})
    assert first.status_code == 201
    second = client.post("/api/watchlist", json={"ticker": "AMD"})
    assert second.status_code == 201
    assert second.json()["status"] == "already_present"


def test_post_watchlist_rejects_empty_ticker(client: TestClient) -> None:
    response = client.post("/api/watchlist", json={"ticker": ""})
    # Pydantic min_length=1 → 422 unprocessable entity
    assert response.status_code == 422


def test_delete_watchlist_removes_existing_ticker(client: TestClient) -> None:
    response = client.delete("/api/watchlist/AAPL")
    assert response.status_code == 200
    assert response.json() == {"ticker": "AAPL", "status": "removed"}
    assert "AAPL" not in watchlist_repo.list_tickers()
    # Market source removes it from the cache too.
    cache = client.app.state.price_cache
    assert cache.get("AAPL") is None


def test_delete_watchlist_unknown_ticker_returns_404(client: TestClient) -> None:
    response = client.delete("/api/watchlist/ZZZZ")
    assert response.status_code == 404


def test_delete_watchlist_normalizes_input(client: TestClient) -> None:
    response = client.delete("/api/watchlist/aapl")
    assert response.status_code == 200
    assert response.json()["ticker"] == "AAPL"
