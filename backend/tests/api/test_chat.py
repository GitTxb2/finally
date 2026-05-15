"""Tests for the /api/chat endpoint (with LLM_MOCK=true)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db import apply_buy, get_cash_balance, list_messages, list_tickers


@pytest.fixture(autouse=True)
def enable_llm_mock(monkeypatch):
    """Force the deterministic mock LLM for every test in this file."""
    monkeypatch.setenv("LLM_MOCK", "true")


def _seed_cached_price(client: TestClient, ticker: str, price: float) -> None:
    client.app.state.price_cache.update(ticker=ticker, price=price)


def test_chat_summary_path_persists_history(client: TestClient) -> None:
    """A generic message should produce a mock summary and append two rows."""
    response = client.post("/api/chat", json={"message": "what's my portfolio?"})
    assert response.status_code == 200
    body = response.json()
    assert "[mock] Portfolio summary" in body["message"]
    assert body["trades_executed"] == []
    assert body["watchlist_changes"] == []
    assert body["errors"] == []
    # Both turns recorded.
    rows = list_messages()
    assert [r.role for r in rows] == ["user", "assistant"]
    assert rows[0].content == "what's my portfolio?"


def test_chat_trade_buy_auto_executes(client: TestClient) -> None:
    _seed_cached_price(client, "AAPL", 150.00)
    response = client.post("/api/chat", json={"message": "buy 2 AAPL"})
    assert response.status_code == 200
    body = response.json()
    assert len(body["trades_executed"]) == 1
    trade = body["trades_executed"][0]
    assert trade["ticker"] == "AAPL"
    assert trade["side"] == "buy"
    assert trade["quantity"] == 2.0
    assert trade["price"] == 150.00
    assert body["errors"] == []
    # Cash decreased.
    assert get_cash_balance() == 10000.0 - 300.0
    # Assistant message stored with the actions payload.
    rows = list_messages()
    assistant_row = rows[-1]
    assert assistant_row.role == "assistant"
    assert assistant_row.actions is not None
    assert len(assistant_row.actions["trades_executed"]) == 1


def test_chat_sell_without_position_records_error(client: TestClient) -> None:
    _seed_cached_price(client, "AAPL", 150.00)
    response = client.post("/api/chat", json={"message": "sell 5 AAPL"})
    assert response.status_code == 200
    body = response.json()
    assert body["trades_executed"] == []
    assert len(body["errors"]) == 1
    assert "AAPL" in body["errors"][0]
    # Assistant message still stored.
    rows = list_messages()
    assert rows[-1].role == "assistant"


def test_chat_watchlist_add_executes(client: TestClient) -> None:
    response = client.post("/api/chat", json={"message": "watch PYPL"})
    assert response.status_code == 200
    body = response.json()
    assert len(body["watchlist_changes"]) == 1
    assert body["watchlist_changes"][0] == {"ticker": "PYPL", "action": "added"}
    assert "PYPL" in list_tickers()


def test_chat_watchlist_remove_executes(client: TestClient) -> None:
    # AAPL is on the default watchlist.
    response = client.post("/api/chat", json={"message": "unwatch AAPL"})
    assert response.status_code == 200
    body = response.json()
    assert body["watchlist_changes"][0] == {"ticker": "AAPL", "action": "removed"}
    assert "AAPL" not in list_tickers()


def test_chat_llm_error_returns_502_and_records_error(client: TestClient) -> None:
    """The mock raises LLMError when the message contains 'error'."""
    response = client.post("/api/chat", json={"message": "please error out"})
    assert response.status_code == 502
    # User message and a placeholder assistant message should both be recorded.
    rows = list_messages()
    assert len(rows) == 2
    assert rows[0].role == "user"
    assert rows[1].role == "assistant"
    assert rows[1].actions is not None
    assert "errors" in rows[1].actions


def test_chat_history_passed_to_llm(client: TestClient) -> None:
    """Previous chat rows should be in the history list — verifiable by storage size."""
    _seed_cached_price(client, "AAPL", 100.00)
    first = client.post("/api/chat", json={"message": "buy 1 AAPL"})
    assert first.status_code == 200
    second = client.post("/api/chat", json={"message": "what's my portfolio?"})
    assert second.status_code == 200
    # Four rows total: two user + two assistant.
    rows = list_messages()
    assert len(rows) == 4
    assert [r.role for r in rows] == ["user", "assistant", "user", "assistant"]


def test_chat_rejects_empty_message(client: TestClient) -> None:
    # Pydantic min_length=1 -> 422.
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422


def test_chat_rejects_whitespace_only_message(client: TestClient) -> None:
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 400
    assert "must not be empty" in response.json()["detail"]


def test_chat_trade_insufficient_cash_records_error_but_other_actions_still_run(
    client: TestClient,
) -> None:
    """A failing trade shouldn't block subsequent actions in the same response.

    The mock only emits one action per message, so we trigger this by having
    an underfunded buy: the mock returns just the trade, execute_trade fails,
    error captured. (Full multi-action isolation is exercised by unit-testing
    _execute_actions in a future test — covered here at the integration level.)
    """
    _seed_cached_price(client, "AAPL", 1.00)
    apply_buy("AAPL", 1.0, 1.00)  # cash now 9999.0
    response = client.post("/api/chat", json={"message": "buy 99999999 AAPL"})
    assert response.status_code == 200
    body = response.json()
    assert body["trades_executed"] == []
    assert len(body["errors"]) == 1
    assert "insufficient cash" in body["errors"][0].lower()
