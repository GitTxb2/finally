"""Repository functions for portfolio_snapshots (P&L chart history)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from .connection import connect
from .schema import DEFAULT_USER_ID, now_iso


@dataclass(frozen=True)
class PortfolioSnapshot:
    id: str
    user_id: str
    total_value: float
    recorded_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "total_value": self.total_value,
            "recorded_at": self.recorded_at,
        }


def record_snapshot(
    total_value: float, user_id: str = DEFAULT_USER_ID
) -> PortfolioSnapshot:
    """Insert a new portfolio snapshot row."""
    snap_id = str(uuid.uuid4())
    ts = now_iso()
    with connect() as conn:
        conn.execute(
            "INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at) "
            "VALUES (?, ?, ?, ?)",
            (snap_id, user_id, total_value, ts),
        )
    return PortfolioSnapshot(
        id=snap_id, user_id=user_id, total_value=total_value, recorded_at=ts
    )


def list_snapshots(
    user_id: str = DEFAULT_USER_ID, limit: int | None = None
) -> list[PortfolioSnapshot]:
    """Return snapshots in chronological order (oldest first), optionally capped.

    The oldest-first order matches how a P&L chart consumes the data.
    """
    query = (
        "SELECT id, user_id, total_value, recorded_at FROM portfolio_snapshots "
        "WHERE user_id = ? ORDER BY recorded_at ASC, id ASC"
    )
    params: list = [user_id]
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
        return [
            PortfolioSnapshot(
                id=row["id"],
                user_id=row["user_id"],
                total_value=row["total_value"],
                recorded_at=row["recorded_at"],
            )
            for row in rows
        ]
