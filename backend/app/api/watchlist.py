"""Watchlist REST endpoints and callable helpers.

The `add_to_watchlist` and `remove_from_watchlist` functions are exposed so
the chat handler (BE-4) can invoke them directly without an HTTP loopback.
Route handlers wrap them with HTTPException translation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.db import watchlist as watchlist_repo
from app.market import MarketDataSource, PriceCache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


class AddTickerRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=10)


@dataclass(frozen=True)
class WatchlistChange:
    ticker: str
    action: str  # "added" | "already_present" | "removed" | "not_present"


def serialize_watchlist(price_cache: PriceCache) -> list[dict]:
    """Return the user's watchlist tickers with their latest prices.

    Shape:
        [{"ticker": "AAPL", "price": 190.50, "previous_price": 190.10,
          "change": 0.40, "change_percent": 0.21, "direction": "up",
          "timestamp": 1715712345.6}, ...]

    A ticker with no cached price yet (newly added, simulator hasn't run a
    step) is returned with `price: null` and the other fields omitted.
    """
    tickers = watchlist_repo.list_tickers()
    result: list[dict] = []
    for ticker in tickers:
        update = price_cache.get(ticker)
        if update is None:
            result.append({"ticker": ticker, "price": None})
        else:
            result.append(update.to_dict())
    return result


async def add_to_watchlist(
    ticker: str,
    price_cache: PriceCache,
    market_source: MarketDataSource,
) -> WatchlistChange:
    """Add `ticker` to the watchlist and start tracking it in the market source.

    Idempotent: if the ticker is already on the watchlist, returns
    `action="already_present"`. Raises `ValueError` on an empty/whitespace ticker.
    """
    cleaned = ticker.strip().upper()
    if not cleaned:
        raise ValueError("ticker must not be empty")
    already = watchlist_repo.contains(cleaned)
    entry = watchlist_repo.add_ticker(cleaned)
    if not already:
        await market_source.add_ticker(entry.ticker)
        logger.info("Watchlist: added %s", entry.ticker)
        return WatchlistChange(ticker=entry.ticker, action="added")
    return WatchlistChange(ticker=entry.ticker, action="already_present")


async def remove_from_watchlist(
    ticker: str,
    price_cache: PriceCache,
    market_source: MarketDataSource,
) -> WatchlistChange:
    """Remove `ticker` from the watchlist and stop tracking it in the market source.

    Idempotent: returns `action="not_present"` if the ticker wasn't on the
    watchlist. The market source also drops the ticker from the price cache.
    """
    cleaned = ticker.strip().upper()
    if not cleaned:
        raise ValueError("ticker must not be empty")
    removed = watchlist_repo.remove_ticker(cleaned)
    if removed:
        await market_source.remove_ticker(cleaned)
        logger.info("Watchlist: removed %s", cleaned)
        return WatchlistChange(ticker=cleaned, action="removed")
    return WatchlistChange(ticker=cleaned, action="not_present")


@router.get("")
async def get_watchlist(request: Request) -> list[dict]:
    """Return all watchlist tickers with their latest prices."""
    price_cache: PriceCache = request.app.state.price_cache
    return serialize_watchlist(price_cache)


@router.post("", status_code=status.HTTP_201_CREATED)
async def post_watchlist(request: Request, body: AddTickerRequest) -> dict:
    """Add a ticker to the watchlist."""
    price_cache: PriceCache = request.app.state.price_cache
    market_source: MarketDataSource = request.app.state.market_source
    try:
        change = await add_to_watchlist(body.ticker, price_cache, market_source)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"ticker": change.ticker, "status": change.action}


@router.delete("/{ticker}")
async def delete_watchlist(request: Request, ticker: str) -> dict:
    """Remove a ticker from the watchlist."""
    price_cache: PriceCache = request.app.state.price_cache
    market_source: MarketDataSource = request.app.state.market_source
    try:
        change = await remove_from_watchlist(ticker, price_cache, market_source)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if change.action == "not_present":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{change.ticker} not on watchlist")
    return {"ticker": change.ticker, "status": change.action}
