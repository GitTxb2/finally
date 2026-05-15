"""Repository functions for the users_profile table."""

from __future__ import annotations

from dataclasses import dataclass

from .connection import connect
from .schema import DEFAULT_CASH_BALANCE, DEFAULT_USER_ID, now_iso


@dataclass(frozen=True)
class UserProfile:
    id: str
    cash_balance: float
    created_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cash_balance": self.cash_balance,
            "created_at": self.created_at,
        }


def get_profile(user_id: str = DEFAULT_USER_ID) -> UserProfile:
    """Return the user's profile. Creates a default row if absent.

    Creation here is a safety net for callers that hit a fresh database
    via a code path that bypasses the seed (e.g., a test that drops a
    table). In normal operation `seed_defaults()` has already populated
    the row.
    """
    with connect() as conn:
        row = conn.execute(
            "SELECT id, cash_balance, created_at FROM users_profile WHERE id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            ts = now_iso()
            conn.execute(
                "INSERT INTO users_profile (id, cash_balance, created_at) VALUES (?, ?, ?)",
                (user_id, DEFAULT_CASH_BALANCE, ts),
            )
            return UserProfile(id=user_id, cash_balance=DEFAULT_CASH_BALANCE, created_at=ts)
        return UserProfile(id=row["id"], cash_balance=row["cash_balance"], created_at=row["created_at"])


def get_cash_balance(user_id: str = DEFAULT_USER_ID) -> float:
    """Convenience: return only the cash balance."""
    return get_profile(user_id).cash_balance


def set_cash_balance(new_balance: float, user_id: str = DEFAULT_USER_ID) -> None:
    """Overwrite the cash balance for a user."""
    with connect() as conn:
        conn.execute(
            "UPDATE users_profile SET cash_balance = ? WHERE id = ?",
            (new_balance, user_id),
        )


def adjust_cash_balance(delta: float, user_id: str = DEFAULT_USER_ID) -> float:
    """Add `delta` to the user's cash balance (negative for spends).

    Returns the new balance. Raises ValueError if it would go negative.
    """
    with connect() as conn:
        row = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?",
            (user_id,),
        ).fetchone()
        current = row["cash_balance"] if row else DEFAULT_CASH_BALANCE
        new_balance = current + delta
        if new_balance < 0:
            raise ValueError(
                f"insufficient cash: {current:.2f} + {delta:.2f} would yield {new_balance:.2f}"
            )
        if row is None:
            conn.execute(
                "INSERT INTO users_profile (id, cash_balance, created_at) VALUES (?, ?, ?)",
                (user_id, new_balance, now_iso()),
            )
        else:
            conn.execute(
                "UPDATE users_profile SET cash_balance = ? WHERE id = ?",
                (new_balance, user_id),
            )
        return new_balance
