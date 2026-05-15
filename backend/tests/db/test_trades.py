"""Tests for the trades repository."""

from __future__ import annotations

import pytest

from app.db import list_trades, record_trade


class TestTrades:
    def test_no_trades_initially(self, db_path):
        assert list_trades() == []

    def test_record_buy(self, db_path):
        trade = record_trade("AAPL", "buy", quantity=10, price=190.0)
        assert trade.ticker == "AAPL"
        assert trade.side == "buy"
        assert trade.quantity == 10
        assert trade.price == 190.0
        assert trade.executed_at
        assert trade.id

    def test_record_sell(self, db_path):
        trade = record_trade("AAPL", "sell", quantity=2, price=205.0)
        assert trade.side == "sell"

    def test_record_trade_normalizes_ticker(self, db_path):
        record_trade("aapl", "buy", quantity=1, price=100.0)
        trades = list_trades()
        assert trades[0].ticker == "AAPL"

    def test_record_trade_rejects_bad_side(self, db_path):
        with pytest.raises(ValueError):
            record_trade("AAPL", "hodl", quantity=1, price=100.0)  # type: ignore[arg-type]

    def test_record_trade_rejects_nonpositive_quantity(self, db_path):
        with pytest.raises(ValueError):
            record_trade("AAPL", "buy", quantity=0, price=100.0)
        with pytest.raises(ValueError):
            record_trade("AAPL", "buy", quantity=-1, price=100.0)

    def test_record_trade_rejects_negative_price(self, db_path):
        with pytest.raises(ValueError):
            record_trade("AAPL", "buy", quantity=1, price=-1.0)

    def test_list_trades_newest_first(self, db_path):
        record_trade("AAPL", "buy", quantity=1, price=100.0)
        record_trade("AAPL", "buy", quantity=1, price=101.0)
        record_trade("AAPL", "buy", quantity=1, price=102.0)
        trades = list_trades()
        prices = [t.price for t in trades]
        # newest first; even with equal timestamps id-DESC keeps order stable
        assert prices[0] == 102.0
        assert len(trades) == 3

    def test_list_trades_filtered_by_ticker(self, db_path):
        record_trade("AAPL", "buy", quantity=1, price=100.0)
        record_trade("MSFT", "buy", quantity=1, price=400.0)
        record_trade("AAPL", "sell", quantity=1, price=110.0)
        aapl = list_trades(ticker="AAPL")
        assert {t.ticker for t in aapl} == {"AAPL"}
        assert len(aapl) == 2

    def test_list_trades_with_limit(self, db_path):
        for i in range(5):
            record_trade("AAPL", "buy", quantity=1, price=100.0 + i)
        trades = list_trades(limit=2)
        assert len(trades) == 2
