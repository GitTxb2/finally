"""Repository functions for the positions table.

A position is the current holdings of a ticker for a user. Buys update
the average cost; sells reduce the quantity. When quantity reaches zero,
the row is removed so a fresh buy gets a clean cost basis.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from .connection import connect
from .schema import DEFAULT_USER_ID, now_iso


@dataclass(frozen=True)
class Position:
    id: str
    user_id: str
    ticker: str
    quantity: float
    avg_cost: float
    updated_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "ticker": self.ticker,
            "quantity": self.quantity,
            "avg_cost": self.avg_cost,
            "updated_at": self.updated_at,
        }


def _row_to_position(row) -> Position:
    return Position(
        id=row["id"],
        user_id=row["user_id"],
        ticker=row["ticker"],
        quantity=row["quantity"],
        avg_cost=row["avg_cost"],
        updated_at=row["updated_at"],
    )


def get_position(ticker: str, user_id: str = DEFAULT_USER_ID) -> Position | None:
    """Return the user's position in a ticker, or None if none is held."""
    ticker = ticker.strip().upper()
    with connect() as conn:
        row = conn.execute(
            "SELECT id, user_id, ticker, quantity, avg_cost, updated_at "
            "FROM positions WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()
        return _row_to_position(row) if row else None


def list_positions(user_id: str = DEFAULT_USER_ID) -> list[Position]:
    """Return all positions held by the user."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, user_id, ticker, quantity, avg_cost, updated_at "
            "FROM positions WHERE user_id = ? ORDER BY ticker",
            (user_id,),
        ).fetchall()
        return [_row_to_position(row) for row in rows]


def apply_buy(
    ticker: str,
    quantity: float,
    price: float,
    user_id: str = DEFAULT_USER_ID,
) -> Position:
    """Apply a buy to the position. Creates the row if absent.

    Average cost is recomputed as a weighted average of existing and new shares.
    Returns the updated position.
    """
    if quantity <= 0:
        raise ValueError(f"buy quantity must be positive, got {quantity}")
    if price < 0:
        raise ValueError(f"price must not be negative, got {price}")
    ticker = ticker.strip().upper()
    ts = now_iso()
    with connect() as conn:
        row = conn.execute(
            "SELECT id, quantity, avg_cost FROM positions WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()
        if row is None:
            new_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (new_id, user_id, ticker, quantity, price, ts),
            )
            return Position(
                id=new_id,
                user_id=user_id,
                ticker=ticker,
                quantity=quantity,
                avg_cost=price,
                updated_at=ts,
            )
        existing_qty = row["quantity"]
        existing_cost = row["avg_cost"]
        new_qty = existing_qty + quantity
        new_cost = ((existing_qty * existing_cost) + (quantity * price)) / new_qty
        conn.execute(
            "UPDATE positions SET quantity = ?, avg_cost = ?, updated_at = ? WHERE id = ?",
            (new_qty, new_cost, ts, row["id"]),
        )
        return Position(
            id=row["id"],
            user_id=user_id,
            ticker=ticker,
            quantity=new_qty,
            avg_cost=new_cost,
            updated_at=ts,
        )


def apply_sell(
    ticker: str,
    quantity: float,
    user_id: str = DEFAULT_USER_ID,
) -> Position | None:
    """Apply a sell to the position.

    The average cost is preserved (FIFO-equivalent for a single basis pool).
    If the resulting quantity is zero (within a tiny epsilon), the row is
    deleted and None is returned. Raises ValueError if the user holds fewer
    shares than requested.
    """
    if quantity <= 0:
        raise ValueError(f"sell quantity must be positive, got {quantity}")
    ticker = ticker.strip().upper()
    ts = now_iso()
    with connect() as conn:
        row = conn.execute(
            "SELECT id, quantity, avg_cost FROM positions WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()
        if row is None:
            raise ValueError(f"no position in {ticker} to sell")
        existing_qty = row["quantity"]
        if quantity > existing_qty + 1e-9:
            raise ValueError(
                f"insufficient shares: holding {existing_qty}, attempted to sell {quantity}"
            )
        new_qty = existing_qty - quantity
        if new_qty <= 1e-9:
            conn.execute("DELETE FROM positions WHERE id = ?", (row["id"],))
            return None
        conn.execute(
            "UPDATE positions SET quantity = ?, updated_at = ? WHERE id = ?",
            (new_qty, ts, row["id"]),
        )
        return Position(
            id=row["id"],
            user_id=user_id,
            ticker=ticker,
            quantity=new_qty,
            avg_cost=row["avg_cost"],
            updated_at=ts,
        )
