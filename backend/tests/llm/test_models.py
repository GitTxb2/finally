"""Schema parsing tests for the LLM structured-output models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.llm.models import ChatResponse, Msg, Trade, WatchlistChange


class TestChatResponse:
    def test_minimal_message_only(self):
        resp = ChatResponse.model_validate({"message": "hello"})
        assert resp.message == "hello"
        assert resp.trades == []
        assert resp.watchlist_changes == []

    def test_full_payload(self):
        payload = {
            "message": "Buying AAPL and watching PYPL.",
            "trades": [{"ticker": "AAPL", "side": "buy", "quantity": 10}],
            "watchlist_changes": [{"ticker": "PYPL", "action": "add"}],
        }
        resp = ChatResponse.model_validate(payload)
        assert resp.trades[0].ticker == "AAPL"
        assert resp.trades[0].side == "buy"
        assert resp.trades[0].quantity == 10.0
        assert resp.watchlist_changes[0].ticker == "PYPL"
        assert resp.watchlist_changes[0].action == "add"

    def test_from_json_string(self):
        raw = '{"message": "ok", "trades": [{"ticker":"TSLA","side":"sell","quantity":2.5}]}'
        resp = ChatResponse.model_validate_json(raw)
        assert resp.trades[0].quantity == 2.5
        assert resp.trades[0].side == "sell"

    def test_message_is_required(self):
        with pytest.raises(ValidationError):
            ChatResponse.model_validate({"trades": []})

    def test_rejects_unknown_side(self):
        with pytest.raises(ValidationError):
            ChatResponse.model_validate(
                {"message": "x", "trades": [{"ticker": "AAPL", "side": "hold", "quantity": 1}]}
            )

    def test_rejects_unknown_action(self):
        with pytest.raises(ValidationError):
            ChatResponse.model_validate(
                {
                    "message": "x",
                    "watchlist_changes": [{"ticker": "PYPL", "action": "ignore"}],
                }
            )

    def test_rejects_non_positive_quantity(self):
        with pytest.raises(ValidationError):
            ChatResponse.model_validate(
                {"message": "x", "trades": [{"ticker": "AAPL", "side": "buy", "quantity": 0}]}
            )


class TestMsg:
    def test_roles(self):
        assert Msg(role="user", content="hi").role == "user"
        assert Msg(role="assistant", content="hello").role == "assistant"
        assert Msg(role="system", content="cfg").role == "system"

    def test_invalid_role(self):
        with pytest.raises(ValidationError):
            Msg(role="tool", content="x")


class TestTradeAndWatchlistChange:
    def test_trade_fractional_quantity(self):
        t = Trade(ticker="AAPL", side="buy", quantity=0.5)
        assert t.quantity == 0.5

    def test_watchlist_remove(self):
        w = WatchlistChange(ticker="NFLX", action="remove")
        assert w.action == "remove"
