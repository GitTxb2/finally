"""Tests for the positions repository."""

from __future__ import annotations

import pytest

from app.db import apply_buy, apply_sell, get_position, list_positions


class TestPositions:
    def test_no_positions_initially(self, db_path):
        assert list_positions() == []
        assert get_position("AAPL") is None

    def test_apply_buy_creates_position(self, db_path):
        pos = apply_buy("AAPL", quantity=10, price=190.0)
        assert pos.ticker == "AAPL"
        assert pos.quantity == 10
        assert pos.avg_cost == 190.0

    def test_apply_buy_normalizes_ticker(self, db_path):
        apply_buy("aapl", quantity=5, price=100.0)
        assert get_position("AAPL") is not None

    def test_apply_buy_aggregates_avg_cost(self, db_path):
        apply_buy("AAPL", quantity=10, price=100.0)
        pos = apply_buy("AAPL", quantity=10, price=200.0)
        assert pos.quantity == 20
        # (10*100 + 10*200) / 20 = 150
        assert pos.avg_cost == 150.0

    def test_apply_buy_rejects_nonpositive_quantity(self, db_path):
        with pytest.raises(ValueError):
            apply_buy("AAPL", quantity=0, price=100.0)
        with pytest.raises(ValueError):
            apply_buy("AAPL", quantity=-1, price=100.0)

    def test_apply_buy_rejects_negative_price(self, db_path):
        with pytest.raises(ValueError):
            apply_buy("AAPL", quantity=1, price=-1.0)

    def test_apply_sell_partial(self, db_path):
        apply_buy("AAPL", quantity=10, price=100.0)
        pos = apply_sell("AAPL", quantity=4)
        assert pos is not None
        assert pos.quantity == 6
        assert pos.avg_cost == 100.0

    def test_apply_sell_complete_removes_row(self, db_path):
        apply_buy("AAPL", quantity=10, price=100.0)
        result = apply_sell("AAPL", quantity=10)
        assert result is None
        assert get_position("AAPL") is None

    def test_apply_sell_no_position_raises(self, db_path):
        with pytest.raises(ValueError):
            apply_sell("AAPL", quantity=1)

    def test_apply_sell_too_many_raises(self, db_path):
        apply_buy("AAPL", quantity=5, price=100.0)
        with pytest.raises(ValueError):
            apply_sell("AAPL", quantity=6)

    def test_apply_sell_rejects_nonpositive(self, db_path):
        apply_buy("AAPL", quantity=5, price=100.0)
        with pytest.raises(ValueError):
            apply_sell("AAPL", quantity=0)
        with pytest.raises(ValueError):
            apply_sell("AAPL", quantity=-1)

    def test_list_positions_ordered(self, db_path):
        apply_buy("MSFT", quantity=1, price=400.0)
        apply_buy("AAPL", quantity=1, price=200.0)
        apply_buy("GOOGL", quantity=1, price=175.0)
        tickers = [p.ticker for p in list_positions()]
        assert tickers == ["AAPL", "GOOGL", "MSFT"]

    def test_buy_after_full_sell_resets_basis(self, db_path):
        apply_buy("AAPL", quantity=5, price=100.0)
        apply_sell("AAPL", quantity=5)
        pos = apply_buy("AAPL", quantity=2, price=300.0)
        assert pos.quantity == 2
        assert pos.avg_cost == 300.0
