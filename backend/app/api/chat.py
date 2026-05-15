"""POST /api/chat — talks to the LLM and auto-executes returned actions."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.portfolio import TradeError, compute_portfolio, execute_trade
from app.api.watchlist import add_to_watchlist, remove_from_watchlist
from app.db import list_messages, list_tickers, record_message
from app.llm import LLMError, Msg
from app.llm import chat as llm_chat
from app.market import MarketDataSource, PriceCache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

HISTORY_LIMIT = 20  # how many recent messages to pass to the LLM


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


def _build_history() -> list[Msg]:
    """Load recent chat history from SQLite, oldest-first."""
    rows = list_messages(limit=HISTORY_LIMIT)
    return [Msg(role=row.role, content=row.content) for row in rows]


def _build_portfolio_context(price_cache: PriceCache) -> dict[str, Any]:
    """Compose the portfolio_context dict the LLM client expects."""
    portfolio = compute_portfolio(price_cache)
    watchlist = []
    for ticker in list_tickers():
        update = price_cache.get(ticker)
        watchlist.append(
            {
                "ticker": ticker,
                "price": update.price if update else None,
            }
        )
    return {
        "cash_balance": portfolio.cash_balance,
        "total_value": portfolio.total_value,
        "total_unrealized_pnl": portfolio.total_unrealized_pnl,
        "positions": [
            {
                "ticker": p.ticker,
                "quantity": p.quantity,
                "avg_cost": p.avg_cost,
                "current_price": p.current_price,
                "unrealized_pnl": p.unrealized_pnl,
            }
            for p in portfolio.positions
        ],
        "watchlist": watchlist,
    }


async def _execute_actions(
    response_trades: list,
    response_watchlist_changes: list,
    price_cache: PriceCache,
    market_source: MarketDataSource,
) -> dict[str, list]:
    """Auto-execute the LLM's requested trades and watchlist changes.

    Each action is processed independently — one failure does not stop the
    others. Successes go into the `trades_executed` / `watchlist_changes`
    arrays; failures go into `errors` with a short string.
    """
    trades_executed: list[dict] = []
    watchlist_changes: list[dict] = []
    errors: list[str] = []

    for t in response_trades:
        try:
            trade = execute_trade(t.ticker, t.side, t.quantity, price_cache)
            trades_executed.append(trade.to_dict())
        except TradeError as exc:
            msg = f"Trade {t.side} {t.quantity} {t.ticker} failed: {exc}"
            logger.warning(msg)
            errors.append(msg)
        except Exception:
            logger.exception("Unexpected error executing LLM trade %r", t)
            errors.append(f"Trade {t.side} {t.quantity} {t.ticker} failed: internal error")

    for wc in response_watchlist_changes:
        try:
            if wc.action == "add":
                change = await add_to_watchlist(wc.ticker, price_cache, market_source)
            elif wc.action == "remove":
                change = await remove_from_watchlist(wc.ticker, price_cache, market_source)
            else:
                errors.append(f"Watchlist change {wc.ticker}: unknown action {wc.action!r}")
                continue
            watchlist_changes.append({"ticker": change.ticker, "action": change.action})
        except ValueError as exc:
            errors.append(f"Watchlist {wc.action} {wc.ticker} failed: {exc}")
        except Exception:
            logger.exception("Unexpected error applying LLM watchlist change %r", wc)
            errors.append(f"Watchlist {wc.action} {wc.ticker} failed: internal error")

    return {
        "trades_executed": trades_executed,
        "watchlist_changes": watchlist_changes,
        "errors": errors,
    }


@router.post("")
async def post_chat(request: Request, body: ChatRequest) -> dict:
    """Handle a chat turn: persist user message, call LLM, execute actions, persist assistant message."""
    price_cache: PriceCache = request.app.state.price_cache
    market_source: MarketDataSource = request.app.state.market_source

    user_text = body.message.strip()
    if not user_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="message must not be empty"
        )

    # Persist the user message BEFORE we call the LLM so history reflects
    # the turn even if the call fails. History for the LLM excludes the
    # current message (the client appends it itself).
    history = _build_history()
    record_message("user", user_text)

    portfolio_context = _build_portfolio_context(price_cache)

    try:
        # llm_chat is sync; run it in a thread so we don't block the event loop.
        response = await asyncio.to_thread(
            llm_chat,
            history=history,
            portfolio_context=portfolio_context,
            user_message=user_text,
        )
    except LLMError as exc:
        logger.warning("LLM call failed: %s", exc)
        # Persist a placeholder assistant turn so the user sees the failure in history.
        error_message = f"Sorry, I couldn't process that ({exc})."
        record_message("assistant", error_message, actions={"errors": [str(exc)]})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    action_results = await _execute_actions(
        response.trades, response.watchlist_changes, price_cache, market_source
    )

    actions_payload = {
        "trades_executed": action_results["trades_executed"],
        "watchlist_changes": action_results["watchlist_changes"],
        "errors": action_results["errors"],
    }
    record_message("assistant", response.message, actions=actions_payload)

    return {
        "message": response.message,
        "trades_executed": action_results["trades_executed"],
        "watchlist_changes": action_results["watchlist_changes"],
        "errors": action_results["errors"],
    }
