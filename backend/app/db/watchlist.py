"""Repository functions for the watchlist table."""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass

from .connection import connect
from .schema import DEFAULT_USER_ID, now_iso


@dataclass(frozen=True)
class WatchlistEntry:
    id: str
    user_id: str
    ticker: str
    added_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "ticker": self.ticker,
            "added_at": self.added_at,
        }


def list_tickers(user_id: str = DEFAULT_USER_ID) -> list[str]:
    """Return the user's watchlist tickers in insertion order."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY added_at, ticker",
            (user_id,),
        ).fetchall()
        return [row["ticker"] for row in rows]


def list_entries(user_id: str = DEFAULT_USER_ID) -> list[WatchlistEntry]:
    """Return the user's full watchlist entries."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, user_id, ticker, added_at FROM watchlist "
            "WHERE user_id = ? ORDER BY added_at, ticker",
            (user_id,),
        ).fetchall()
        return [
            WatchlistEntry(
                id=row["id"],
                user_id=row["user_id"],
                ticker=row["ticker"],
                added_at=row["added_at"],
            )
            for row in rows
        ]


def add_ticker(ticker: str, user_id: str = DEFAULT_USER_ID) -> WatchlistEntry:
    """Add a ticker to the user's watchlist.

    Ticker is normalized to uppercase. Returns the (new or existing) entry.
    """
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker must not be empty")
    with connect() as conn:
        try:
            entry_id = str(uuid.uuid4())
            ts = now_iso()
            conn.execute(
                "INSERT INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
                (entry_id, user_id, ticker, ts),
            )
            return WatchlistEntry(id=entry_id, user_id=user_id, ticker=ticker, added_at=ts)
        except sqlite3.IntegrityError:
            row = conn.execute(
                "SELECT id, user_id, ticker, added_at FROM watchlist "
                "WHERE user_id = ? AND ticker = ?",
                (user_id, ticker),
            ).fetchone()
            return WatchlistEntry(
                id=row["id"],
                user_id=row["user_id"],
                ticker=row["ticker"],
                added_at=row["added_at"],
            )


def remove_ticker(ticker: str, user_id: str = DEFAULT_USER_ID) -> bool:
    """Remove a ticker from the user's watchlist. Returns True if a row was removed."""
    ticker = ticker.strip().upper()
    with connect() as conn:
        cur = conn.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        )
        return cur.rowcount > 0


def contains(ticker: str, user_id: str = DEFAULT_USER_ID) -> bool:
    """Check whether a ticker is on the user's watchlist."""
    ticker = ticker.strip().upper()
    with connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM watchlist WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()
        return row is not None
