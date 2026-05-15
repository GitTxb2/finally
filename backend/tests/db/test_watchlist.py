"""Tests for the watchlist repository."""

from __future__ import annotations

import pytest

from app.db import (
    DEFAULT_WATCHLIST,
    add_ticker,
    contains,
    list_entries,
    list_tickers,
    remove_ticker,
)


class TestWatchlist:
    def test_list_tickers_returns_seeded_defaults(self, db_path):
        tickers = list_tickers()
        assert sorted(tickers) == sorted(DEFAULT_WATCHLIST)

    def test_add_ticker(self, db_path):
        entry = add_ticker("PYPL")
        assert entry.ticker == "PYPL"
        assert "PYPL" in list_tickers()

    def test_add_ticker_normalizes_to_uppercase(self, db_path):
        add_ticker("pypl")
        assert "PYPL" in list_tickers()

    def test_add_ticker_strips_whitespace(self, db_path):
        add_ticker("  ibm  ")
        assert "IBM" in list_tickers()

    def test_add_ticker_is_idempotent(self, db_path):
        e1 = add_ticker("PYPL")
        e2 = add_ticker("PYPL")
        assert e1.id == e2.id
        assert list_tickers().count("PYPL") == 1

    def test_add_empty_ticker_raises(self, db_path):
        with pytest.raises(ValueError):
            add_ticker("")
        with pytest.raises(ValueError):
            add_ticker("   ")

    def test_remove_ticker(self, db_path):
        assert remove_ticker("AAPL") is True
        assert "AAPL" not in list_tickers()

    def test_remove_ticker_missing_returns_false(self, db_path):
        assert remove_ticker("DOES_NOT_EXIST") is False

    def test_remove_ticker_normalizes_case(self, db_path):
        assert remove_ticker("aapl") is True
        assert "AAPL" not in list_tickers()

    def test_contains(self, db_path):
        assert contains("AAPL")
        assert contains("aapl")
        assert not contains("NOPE")

    def test_list_entries_have_fields(self, db_path):
        entries = list_entries()
        assert len(entries) == len(DEFAULT_WATCHLIST)
        for entry in entries:
            assert entry.id
            assert entry.user_id == "default"
            assert entry.ticker in DEFAULT_WATCHLIST
            assert entry.added_at
