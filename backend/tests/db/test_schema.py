"""Tests for schema creation, idempotency, and seeding."""

from __future__ import annotations

import sqlite3

import pytest

from app.db import connect
from app.db.schema import (
    DEFAULT_CASH_BALANCE,
    DEFAULT_USER_ID,
    DEFAULT_WATCHLIST,
    create_schema,
    ensure_initialized,
    seed_defaults,
)


class TestSchemaCreation:
    def test_creates_all_expected_tables(self, db_path):
        with connect() as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            tables = {row["name"] for row in rows}
            assert {
                "users_profile",
                "watchlist",
                "positions",
                "trades",
                "portfolio_snapshots",
                "chat_messages",
            }.issubset(tables)

    def test_create_schema_is_idempotent(self, db_path):
        with connect() as conn:
            create_schema(conn)
            create_schema(conn)
            count = conn.execute(
                "SELECT COUNT(*) AS n FROM sqlite_master WHERE type='table'"
            ).fetchone()["n"]
            assert count >= 6

    def test_pragmas_applied(self, db_path):
        with connect() as conn:
            fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
            journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert fk == 1
            assert journal.lower() == "wal"


class TestSeedData:
    def test_default_user_seeded(self, db_path):
        with connect() as conn:
            row = conn.execute(
                "SELECT id, cash_balance FROM users_profile WHERE id = ?",
                (DEFAULT_USER_ID,),
            ).fetchone()
            assert row is not None
            assert row["id"] == DEFAULT_USER_ID
            assert row["cash_balance"] == DEFAULT_CASH_BALANCE

    def test_default_watchlist_seeded(self, db_path):
        with connect() as conn:
            rows = conn.execute(
                "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY ticker",
                (DEFAULT_USER_ID,),
            ).fetchall()
            tickers = sorted(row["ticker"] for row in rows)
            assert tickers == sorted(DEFAULT_WATCHLIST)

    def test_seed_defaults_is_idempotent(self, db_path):
        with connect() as conn:
            seed_defaults(conn)
            seed_defaults(conn)
            count_users = conn.execute(
                "SELECT COUNT(*) AS n FROM users_profile WHERE id = ?",
                (DEFAULT_USER_ID,),
            ).fetchone()["n"]
            count_watchlist = conn.execute(
                "SELECT COUNT(*) AS n FROM watchlist WHERE user_id = ?",
                (DEFAULT_USER_ID,),
            ).fetchone()["n"]
            assert count_users == 1
            assert count_watchlist == len(DEFAULT_WATCHLIST)

    def test_ensure_initialized_idempotent(self, db_path):
        with connect() as conn:
            ensure_initialized(conn)
            ensure_initialized(conn)
            count_watchlist = conn.execute(
                "SELECT COUNT(*) AS n FROM watchlist WHERE user_id = ?",
                (DEFAULT_USER_ID,),
            ).fetchone()["n"]
            assert count_watchlist == len(DEFAULT_WATCHLIST)


class TestConstraints:
    def test_watchlist_unique_user_ticker(self, db_path):
        import uuid

        with connect() as conn:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO watchlist (id, user_id, ticker, added_at) "
                    "VALUES (?, ?, ?, ?)",
                    (str(uuid.uuid4()), DEFAULT_USER_ID, "AAPL", "now"),
                )

    def test_positions_unique_user_ticker(self, db_path):
        import uuid

        with connect() as conn:
            conn.execute(
                "INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), DEFAULT_USER_ID, "AAPL", 10, 100.0, "now"),
            )
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), DEFAULT_USER_ID, "AAPL", 5, 110.0, "now"),
                )

    def test_trades_side_check_constraint(self, db_path):
        import uuid

        with connect() as conn:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), DEFAULT_USER_ID, "AAPL", "hodl", 1, 100.0, "now"),
                )

    def test_chat_role_check_constraint(self, db_path):
        import uuid

        with connect() as conn:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO chat_messages (id, user_id, role, content, actions, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), DEFAULT_USER_ID, "system", "hello", None, "now"),
                )
