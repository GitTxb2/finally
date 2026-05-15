"""Portfolio REST endpoints and trade-execution helpers.

`execute_trade` and `compute_portfolio` are exposed at module level so the
chat handler (BE-4) can call them without an HTTP loopback.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.db import (
    Trade,
    adjust_cash_balance,
    apply_buy,
    apply_sell,
    get_cash_balance,
    list_positions,
    list_snapshots,
    record_snapshot,
    record_trade,
)
from app.market import PriceCache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

TradeSide = Literal["buy", "sell"]


class TradeRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=10)
    quantity: float = Field(gt=0)
    side: TradeSide


@dataclass(frozen=True)
class PortfolioPosition:
    ticker: str
    quantity: float
    avg_cost: float
    current_price: float | None
    market_value: float | None
    unrealized_pnl: float | None
    unrealized_pnl_pct: float | None


@dataclass(frozen=True)
class PortfolioSnapshot:
    cash_balance: float
    positions: list[PortfolioPosition]
    total_market_value: float
    total_value: float
    total_unrealized_pnl: float

    def to_dict(self) -> dict:
        return {
            "cash_balance": self.cash_balance,
            "positions": [
                {
                    "ticker": p.ticker,
                    "quantity": p.quantity,
                    "avg_cost": p.avg_cost,
                    "current_price": p.current_price,
                    "market_value": p.market_value,
                    "unrealized_pnl": p.unrealized_pnl,
                    "unrealized_pnl_pct": p.unrealized_pnl_pct,
                }
                for p in self.positions
            ],
            "total_market_value": self.total_market_value,
            "total_value": self.total_value,
            "total_unrealized_pnl": self.total_unrealized_pnl,
        }


def compute_portfolio(price_cache: PriceCache) -> PortfolioSnapshot:
    """Compose the user's current portfolio snapshot from DB state + live prices.

    Positions whose ticker has no cached price (e.g. a brand-new ticker the
    simulator hasn't priced yet) are returned with `current_price=None` and
    contribute 0 to the total market value.
    """
    cash = get_cash_balance()
    raw_positions = list_positions()
    positions: list[PortfolioPosition] = []
    total_market_value = 0.0
    total_unrealized_pnl = 0.0

    for pos in raw_positions:
        price = price_cache.get_price(pos.ticker)
        if price is None:
            positions.append(
                PortfolioPosition(
                    ticker=pos.ticker,
                    quantity=pos.quantity,
                    avg_cost=pos.avg_cost,
                    current_price=None,
                    market_value=None,
                    unrealized_pnl=None,
                    unrealized_pnl_pct=None,
                )
            )
            continue
        market_value = pos.quantity * price
        pnl = (price - pos.avg_cost) * pos.quantity
        pnl_pct = ((price - pos.avg_cost) / pos.avg_cost * 100.0) if pos.avg_cost > 0 else 0.0
        positions.append(
            PortfolioPosition(
                ticker=pos.ticker,
                quantity=pos.quantity,
                avg_cost=pos.avg_cost,
                current_price=price,
                market_value=market_value,
                unrealized_pnl=pnl,
                unrealized_pnl_pct=pnl_pct,
            )
        )
        total_market_value += market_value
        total_unrealized_pnl += pnl

    return PortfolioSnapshot(
        cash_balance=cash,
        positions=positions,
        total_market_value=total_market_value,
        total_value=cash + total_market_value,
        total_unrealized_pnl=total_unrealized_pnl,
    )


class TradeError(Exception):
    """Raised when a trade cannot be executed (validation failure)."""


def execute_trade(
    ticker: str,
    side: str,
    quantity: float,
    price_cache: PriceCache,
) -> Trade:
    """Execute a market order against the current cached price.

    Validation:
      - `side` must be "buy" or "sell"
      - `quantity` must be positive
      - the ticker must have a cached price
      - buys require sufficient cash
      - sells require sufficient shares

    On success, updates positions, adjusts cash, records the trade, and writes
    a portfolio snapshot. Returns the persisted Trade. Raises TradeError on
    any validation failure (no DB writes occur).
    """
    if side not in ("buy", "sell"):
        raise TradeError(f"side must be 'buy' or 'sell', got {side!r}")
    if quantity <= 0:
        raise TradeError(f"quantity must be positive, got {quantity}")

    cleaned = ticker.strip().upper()
    if not cleaned:
        raise TradeError("ticker must not be empty")

    price = price_cache.get_price(cleaned)
    if price is None:
        raise TradeError(f"no cached price for {cleaned} — add it to the watchlist first")

    notional = price * quantity

    if side == "buy":
        cash = get_cash_balance()
        if notional > cash + 1e-9:
            raise TradeError(
                f"insufficient cash: need ${notional:.2f}, have ${cash:.2f}"
            )
        # Cash check above prevents adjust_cash_balance from raising, but if
        # the simulator updated the price between the check and here, fall
        # back to the DB's own guard.
        try:
            adjust_cash_balance(-notional)
        except ValueError as exc:
            raise TradeError(str(exc)) from exc
        apply_buy(cleaned, quantity, price)
    else:  # sell
        try:
            apply_sell(cleaned, quantity)
        except ValueError as exc:
            raise TradeError(str(exc)) from exc
        adjust_cash_balance(+notional)

    trade = record_trade(cleaned, side, quantity, price)

    # Record a fresh snapshot so the P&L chart reflects the trade immediately.
    snapshot = compute_portfolio(price_cache)
    record_snapshot(snapshot.total_value)

    logger.info(
        "Trade executed: %s %.4f %s @ $%.2f (notional $%.2f)",
        side,
        quantity,
        cleaned,
        price,
        notional,
    )
    return trade


@router.get("")
async def get_portfolio(request: Request) -> dict:
    """Return the user's full portfolio snapshot."""
    price_cache: PriceCache = request.app.state.price_cache
    return compute_portfolio(price_cache).to_dict()


@router.post("/trade")
async def post_trade(request: Request, body: TradeRequest) -> dict:
    """Execute a market order at the current cached price."""
    price_cache: PriceCache = request.app.state.price_cache
    try:
        trade = execute_trade(body.ticker, body.side, body.quantity, price_cache)
    except TradeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    portfolio = compute_portfolio(price_cache)
    return {"trade": trade.to_dict(), "portfolio": portfolio.to_dict()}


@router.get("/history")
async def get_history(request: Request, limit: int | None = None) -> dict:
    """Return portfolio value snapshots for the P&L chart.

    Snapshots are ordered oldest-first. Optionally cap with `?limit=N` to
    return the most recent N points (still oldest-first within that window).
    """
    snapshots = list_snapshots(limit=limit)
    return {
        "snapshots": [
            {"total_value": s.total_value, "recorded_at": s.recorded_at}
            for s in snapshots
        ]
    }
