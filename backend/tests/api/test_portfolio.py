"""Tests for the /api/portfolio REST endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.db import (
    apply_buy,
    get_cash_balance,
    list_positions,
    list_snapshots,
    list_trades,
)


def _seed_cached_price(client: TestClient, ticker: str, price: float) -> None:
    """Force a price into the cache so trades against this ticker can execute."""
    cache = client.app.state.price_cache
    cache.update(ticker=ticker, price=price)


def test_get_portfolio_fresh_state(client: TestClient) -> None:
    response = client.get("/api/portfolio")
    assert response.status_code == 200
    body = response.json()
    assert body["cash_balance"] == 10000.0
    assert body["positions"] == []
    assert body["total_market_value"] == 0.0
    assert body["total_value"] == 10000.0
    assert body["total_unrealized_pnl"] == 0.0


def test_get_portfolio_with_position(client: TestClient) -> None:
    _seed_cached_price(client, "AAPL", 200.00)
    apply_buy("AAPL", 5.0, 190.00)

    response = client.get("/api/portfolio")
    assert response.status_code == 200
    body = response.json()
    assert len(body["positions"]) == 1
    pos = body["positions"][0]
    assert pos["ticker"] == "AAPL"
    assert pos["quantity"] == 5.0
    assert pos["avg_cost"] == 190.00
    assert pos["current_price"] == 200.00
    assert pos["market_value"] == 1000.00
    assert pos["unrealized_pnl"] == 50.0
    assert abs(pos["unrealized_pnl_pct"] - (10.0 / 190.0 * 100.0)) < 1e-9
    assert body["total_market_value"] == 1000.00
    assert body["total_unrealized_pnl"] == 50.0


def test_post_trade_buy_succeeds(client: TestClient) -> None:
    _seed_cached_price(client, "AAPL", 200.00)
    response = client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "quantity": 3, "side": "buy"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["trade"]["ticker"] == "AAPL"
    assert body["trade"]["side"] == "buy"
    assert body["trade"]["quantity"] == 3
    assert body["trade"]["price"] == 200.00
    # Cash decreased by notional.
    assert get_cash_balance() == 10000.0 - 600.0
    # Position created.
    positions = list_positions()
    assert len(positions) == 1
    assert positions[0].ticker == "AAPL"
    assert positions[0].quantity == 3.0
    assert positions[0].avg_cost == 200.00
    # Trade row recorded.
    trades = list_trades()
    assert len(trades) == 1
    # A snapshot was written (so the P&L chart updates immediately).
    assert len(list_snapshots()) >= 1


def test_post_trade_sell_succeeds(client: TestClient) -> None:
    _seed_cached_price(client, "AAPL", 200.00)
    apply_buy("AAPL", 5.0, 180.00)  # held at $180 avg cost

    response = client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "quantity": 2, "side": "sell"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["trade"]["side"] == "sell"
    # Cash increased by sale proceeds.
    assert get_cash_balance() == 10000.0 + 400.0  # 2 * 200
    positions = list_positions()
    assert positions[0].quantity == 3.0
    # avg_cost preserved on partial sells.
    assert positions[0].avg_cost == 180.00


def test_post_trade_sell_all_removes_position(client: TestClient) -> None:
    _seed_cached_price(client, "AAPL", 200.00)
    apply_buy("AAPL", 4.0, 180.00)

    response = client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "quantity": 4, "side": "sell"},
    )
    assert response.status_code == 200
    assert list_positions() == []


def test_post_trade_buy_insufficient_cash_returns_400(client: TestClient) -> None:
    _seed_cached_price(client, "AAPL", 200.00)
    response = client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "quantity": 100, "side": "buy"},
    )
    assert response.status_code == 400
    assert "insufficient cash" in response.json()["detail"].lower()
    # No state was changed.
    assert get_cash_balance() == 10000.0
    assert list_positions() == []
    assert list_trades() == []


def test_post_trade_sell_insufficient_shares_returns_400(client: TestClient) -> None:
    _seed_cached_price(client, "AAPL", 200.00)
    response = client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "quantity": 1, "side": "sell"},
    )
    assert response.status_code == 400
    # No state changed.
    assert get_cash_balance() == 10000.0
    assert list_trades() == []


def test_post_trade_unknown_ticker_returns_400(client: TestClient) -> None:
    response = client.post(
        "/api/portfolio/trade",
        json={"ticker": "ZZZZ", "quantity": 1, "side": "buy"},
    )
    # ZZZZ has no cached price.
    assert response.status_code == 400
    assert "no cached price" in response.json()["detail"].lower()


def test_post_trade_invalid_payload_returns_422(client: TestClient) -> None:
    # Negative quantity.
    bad_qty = client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "quantity": -5, "side": "buy"},
    )
    assert bad_qty.status_code == 422
    # Bad side.
    bad_side = client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "quantity": 1, "side": "trade"},
    )
    assert bad_side.status_code == 422


def test_get_history_empty(client: TestClient) -> None:
    response = client.get("/api/portfolio/history")
    assert response.status_code == 200
    assert response.json() == {"snapshots": []}


def test_get_history_after_trade(client: TestClient) -> None:
    _seed_cached_price(client, "AAPL", 200.00)
    client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "quantity": 1, "side": "buy"},
    )
    response = client.get("/api/portfolio/history")
    assert response.status_code == 200
    snapshots = response.json()["snapshots"]
    assert len(snapshots) >= 1
    assert snapshots[0]["total_value"] > 0
    assert "recorded_at" in snapshots[0]


def test_get_history_respects_limit(client: TestClient) -> None:
    _seed_cached_price(client, "AAPL", 200.00)
    # Generate 3 snapshots via 3 trades.
    for _ in range(3):
        client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "quantity": 1, "side": "buy"},
        )
    response = client.get("/api/portfolio/history?limit=2")
    assert response.status_code == 200
    snapshots = response.json()["snapshots"]
    assert len(snapshots) == 2
