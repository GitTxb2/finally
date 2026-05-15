"""Tests for the users_profile repository."""

from __future__ import annotations

import pytest

from app.db import (
    DEFAULT_CASH_BALANCE,
    DEFAULT_USER_ID,
    adjust_cash_balance,
    get_cash_balance,
    get_profile,
    set_cash_balance,
)


class TestUserProfile:
    def test_get_profile_returns_seeded_default(self, db_path):
        profile = get_profile()
        assert profile.id == DEFAULT_USER_ID
        assert profile.cash_balance == DEFAULT_CASH_BALANCE
        assert profile.created_at

    def test_get_cash_balance(self, db_path):
        assert get_cash_balance() == DEFAULT_CASH_BALANCE

    def test_set_cash_balance(self, db_path):
        set_cash_balance(5000.0)
        assert get_cash_balance() == 5000.0

    def test_adjust_cash_balance_positive(self, db_path):
        new = adjust_cash_balance(250.0)
        assert new == DEFAULT_CASH_BALANCE + 250.0
        assert get_cash_balance() == DEFAULT_CASH_BALANCE + 250.0

    def test_adjust_cash_balance_negative(self, db_path):
        new = adjust_cash_balance(-1000.0)
        assert new == DEFAULT_CASH_BALANCE - 1000.0

    def test_adjust_cash_balance_rejects_negative_result(self, db_path):
        with pytest.raises(ValueError):
            adjust_cash_balance(-(DEFAULT_CASH_BALANCE + 1))
        assert get_cash_balance() == DEFAULT_CASH_BALANCE

    def test_get_profile_creates_when_missing(self, db_path):
        profile = get_profile("alice")
        assert profile.id == "alice"
        assert profile.cash_balance == DEFAULT_CASH_BALANCE
        assert get_cash_balance("alice") == DEFAULT_CASH_BALANCE
