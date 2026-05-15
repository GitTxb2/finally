"""Repository functions for the trades table (append-only log)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

from .connection import connect
from .schema import DEFAULT_USER_ID, now_iso

TradeSide = Literal["buy", "sell"]


@dataclass(frozen=True)
class Trade:
    id: str
    user_id: str
    ticker: str
    side: TradeSide
    quantity: float
    price: float
    executed_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "ticker": self.ticker,
            "side": self.side,
            "quantity": self.quantity,
            "price": self.price,
            "executed_at": self.executed_at,
        }


def _row_to_trade(row) -> Trade:
    return Trade(
        id=row["id"],
        user_id=row["user_id"],
        ticker=row["ticker"],
        side=row["side"],
        quantity=row["quantity"],
        price=row["price"],
        executed_at=row["executed_at"],
    )


def record_trade(
    ticker: str,
    side: TradeSide,
    quantity: float,
    price: float,
    user_id: str = DEFAULT_USER_ID,
) -> Trade:
    """Append a trade to the log. Returns the persisted row."""
    if side not in ("buy", "sell"):
        raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")
    if quantity <= 0:
        raise ValueError(f"quantity must be positive, got {quantity}")
    if price < 0:
        raise ValueError(f"price must not be negative, got {price}")
    ticker = ticker.strip().upper()
    trade_id = str(uuid.uuid4())
    ts = now_iso()
    with connect() as conn:
        conn.execute(
            "INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (trade_id, user_id, ticker, side, quantity, price, ts),
        )
    return Trade(
        id=trade_id,
        user_id=user_id,
        ticker=ticker,
        side=side,
        quantity=quantity,
        price=price,
        executed_at=ts,
    )


def list_trades(
    user_id: str = DEFAULT_USER_ID,
    ticker: str | None = None,
    limit: int | None = None,
) -> list[Trade]:
    """Return trades for the user, most recent first.

    Optionally filtered to a specific ticker, optionally capped at `limit` rows.
    """
    query = (
        "SELECT id, user_id, ticker, side, quantity, price, executed_at "
        "FROM trades WHERE user_id = ?"
    )
    params: list = [user_id]
    if ticker is not None:
        query += " AND ticker = ?"
        params.append(ticker.strip().upper())
    query += " ORDER BY executed_at DESC, id DESC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
        return [_row_to_trade(row) for row in rows]
