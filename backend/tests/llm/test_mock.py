"""Tests for the deterministic mock LLM (LLM_MOCK=true path)."""

from __future__ import annotations

import pytest

from app.llm import chat
from app.llm.mock import mock_chat
from app.llm.models import LLMError


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")


@pytest.fixture
def portfolio_ctx():
    return {
        "cash_balance": 10000.0,
        "total_value": 12345.67,
        "positions": [
            {"ticker": "AAPL", "quantity": 5, "avg_cost": 190.0},
            {"ticker": "MSFT", "quantity": 2, "avg_cost": 400.0},
        ],
    }


class TestMockTradeTriggers:
    def test_buy_phrase(self, portfolio_ctx):
        resp = mock_chat("please buy 5 AAPL right now", portfolio_ctx)
        assert len(resp.trades) == 1
        assert resp.trades[0].ticker == "AAPL"
        assert resp.trades[0].side == "buy"
        assert resp.trades[0].quantity == 5.0
        assert resp.watchlist_changes == []

    def test_sell_phrase(self, portfolio_ctx):
        resp = mock_chat("sell 2.5 TSLA", portfolio_ctx)
        assert resp.trades[0].side == "sell"
        assert resp.trades[0].ticker == "TSLA"
        assert resp.trades[0].quantity == 2.5

    def test_ticker_uppercased(self, portfolio_ctx):
        resp = mock_chat("buy 1 aapl", portfolio_ctx)
        assert resp.trades[0].ticker == "AAPL"


class TestMockWatchlistTriggers:
    def test_add_phrase(self, portfolio_ctx):
        resp = mock_chat("add PYPL to my list", portfolio_ctx)
        assert resp.trades == []
        assert len(resp.watchlist_changes) == 1
        assert resp.watchlist_changes[0].ticker == "PYPL"
        assert resp.watchlist_changes[0].action == "add"

    def test_watch_phrase(self, portfolio_ctx):
        resp = mock_chat("watch SHOP", portfolio_ctx)
        assert resp.watchlist_changes[0].action == "add"
        assert resp.watchlist_changes[0].ticker == "SHOP"

    def test_remove_phrase(self, portfolio_ctx):
        resp = mock_chat("remove NFLX", portfolio_ctx)
        assert resp.watchlist_changes[0].action == "remove"
        assert resp.watchlist_changes[0].ticker == "NFLX"

    def test_unwatch_phrase(self, portfolio_ctx):
        resp = mock_chat("unwatch META please", portfolio_ctx)
        assert resp.watchlist_changes[0].action == "remove"
        assert resp.watchlist_changes[0].ticker == "META"

    def test_remove_takes_precedence_over_add(self, portfolio_ctx):
        # If both kinds of phrases appear, the regexes still match independently;
        # remove is checked first, so removal wins.
        resp = mock_chat("add PYPL and remove NFLX", portfolio_ctx)
        assert len(resp.watchlist_changes) == 1
        assert resp.watchlist_changes[0].action == "remove"
        assert resp.watchlist_changes[0].ticker == "NFLX"


class TestMockFallback:
    def test_portfolio_summary_when_no_trigger(self, portfolio_ctx):
        resp = mock_chat("how am I doing today?", portfolio_ctx)
        assert resp.trades == []
        assert resp.watchlist_changes == []
        assert "[mock]" in resp.message
        assert "positions=2" in resp.message
        assert "10,000" in resp.message

    def test_portfolio_summary_empty_context(self):
        resp = mock_chat("hello", {})
        assert resp.trades == []
        assert "positions=0" in resp.message


class TestMockError:
    def test_error_keyword_raises(self, portfolio_ctx):
        with pytest.raises(LLMError):
            mock_chat("simulate an error please", portfolio_ctx)

    def test_fail_keyword_raises(self, portfolio_ctx):
        with pytest.raises(LLMError):
            mock_chat("make this fail", portfolio_ctx)


class TestChatRespectsMockEnv:
    def test_chat_uses_mock_when_env_set(self, mock_env, portfolio_ctx):
        resp = chat(portfolio_context=portfolio_ctx, user_message="buy 3 NVDA")
        assert resp.trades[0].ticker == "NVDA"
        assert resp.trades[0].quantity == 3.0

    def test_chat_mock_mode_without_api_key(self, mock_env, monkeypatch, portfolio_ctx):
        # Mock mode must not require OPENROUTER_API_KEY.
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        resp = chat(portfolio_context=portfolio_ctx, user_message="hello")
        assert resp.message

    def test_chat_rejects_empty_message(self, mock_env, portfolio_ctx):
        with pytest.raises(LLMError):
            chat(portfolio_context=portfolio_ctx, user_message="")

    def test_chat_rejects_whitespace_message(self, mock_env, portfolio_ctx):
        with pytest.raises(LLMError):
            chat(portfolio_context=portfolio_ctx, user_message="   ")
