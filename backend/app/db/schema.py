"""Database schema definition and lazy initialization."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

DEFAULT_USER_ID = "default"
DEFAULT_CASH_BALANCE = 10000.0
DEFAULT_WATCHLIST = (
    "AAPL",
    "GOOGL",
    "MSFT",
    "AMZN",
    "TSLA",
    "NVDA",
    "META",
    "JPM",
    "V",
    "NFLX",
)

SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS users_profile (
        id TEXT PRIMARY KEY,
        cash_balance REAL NOT NULL DEFAULT 10000.0,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS watchlist (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL DEFAULT 'default',
        ticker TEXT NOT NULL,
        added_at TEXT NOT NULL,
        UNIQUE (user_id, ticker)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS positions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL DEFAULT 'default',
        ticker TEXT NOT NULL,
        quantity REAL NOT NULL,
        avg_cost REAL NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (user_id, ticker)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS trades (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL DEFAULT 'default',
        ticker TEXT NOT NULL,
        side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
        quantity REAL NOT NULL,
        price REAL NOT NULL,
        executed_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS portfolio_snapshots (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL DEFAULT 'default',
        total_value REAL NOT NULL,
        recorded_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS chat_messages (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL DEFAULT 'default',
        role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
        content TEXT NOT NULL,
        actions TEXT,
        created_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_trades_user_ticker ON trades(user_id, ticker)",
    "CREATE INDEX IF NOT EXISTS idx_trades_executed_at ON trades(executed_at)",
    "CREATE INDEX IF NOT EXISTS idx_snapshots_user_recorded ON portfolio_snapshots(user_id, recorded_at)",
    "CREATE INDEX IF NOT EXISTS idx_chat_user_created ON chat_messages(user_id, created_at)",
)


def now_iso() -> str:
    """ISO-8601 UTC timestamp string used for all created_at / updated_at columns."""
    return datetime.now(UTC).isoformat()


def create_schema(conn: sqlite3.Connection) -> None:
    """Apply every CREATE TABLE / CREATE INDEX statement (idempotent)."""
    with conn:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)


def seed_defaults(conn: sqlite3.Connection) -> None:
    """Insert the default user profile and watchlist tickers if absent.

    Idempotent: re-running has no effect once the rows are present.
    """
    import uuid

    ts = now_iso()
    with conn:
        conn.execute(
            "INSERT OR IGNORE INTO users_profile (id, cash_balance, created_at) "
            "VALUES (?, ?, ?)",
            (DEFAULT_USER_ID, DEFAULT_CASH_BALANCE, ts),
        )
        for ticker in DEFAULT_WATCHLIST:
            conn.execute(
                "INSERT OR IGNORE INTO watchlist (id, user_id, ticker, added_at) "
                "VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), DEFAULT_USER_ID, ticker, ts),
            )


def ensure_initialized(conn: sqlite3.Connection) -> None:
    """Create the schema and seed defaults if either is missing.

    Safe to call on every connection; both operations are idempotent.
    """
    create_schema(conn)
    seed_defaults(conn)
