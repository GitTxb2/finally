"""Deterministic mock LLM responses for E2E tests and no-key development.

Active when env var LLM_MOCK=true.

Trigger phrases (case-insensitive, matched against the user's latest message):

    "buy <N> <TICKER>"      -> trades: [{ticker, side:"buy",  quantity:N}]
    "sell <N> <TICKER>"     -> trades: [{ticker, side:"sell", quantity:N}]
    "add <TICKER>"          -> watchlist_changes: [{ticker, action:"add"}]
    "remove <TICKER>"       -> watchlist_changes: [{ticker, action:"remove"}]
    "watch <TICKER>"        -> watchlist_changes: [{ticker, action:"add"}]
    "unwatch <TICKER>"      -> watchlist_changes: [{ticker, action:"remove"}]
    "error" / "fail"        -> raises LLMError (for error-path tests)

Anything else returns a brief portfolio summary echoed from portfolio_context
(cash balance + position count if present).

Tickers are 1-5 uppercase letters. Quantities support decimals.
Multiple phrases in one message are NOT combined; the first match wins.
"""

from __future__ import annotations

import re
from typing import Any

from .models import ChatResponse, LLMError, Trade, WatchlistChange

_TRADE_RE = re.compile(r"\b(buy|sell)\s+(\d+(?:\.\d+)?)\s+([A-Za-z]{1,5})\b", re.IGNORECASE)
_WATCHLIST_ADD_RE = re.compile(r"\b(?:add|watch)\s+([A-Za-z]{1,5})\b", re.IGNORECASE)
_WATCHLIST_REMOVE_RE = re.compile(r"\b(?:remove|unwatch)\s+([A-Za-z]{1,5})\b", re.IGNORECASE)


def mock_chat(user_message: str, portfolio_context: dict[str, Any]) -> ChatResponse:
    """Return a deterministic ChatResponse based on simple keyword matching."""
    text = user_message.strip()
    lowered = text.lower()

    if "error" in lowered or "fail" in lowered:
        raise LLMError("mock LLM error (triggered by 'error'/'fail' in user message)")

    trade_match = _TRADE_RE.search(text)
    if trade_match:
        side, qty_str, ticker = trade_match.groups()
        return ChatResponse(
            message=f"Executing {side.lower()} of {qty_str} {ticker.upper()}.",
            trades=[
                Trade(ticker=ticker.upper(), side=side.lower(), quantity=float(qty_str))
            ],
        )

    remove_match = _WATCHLIST_REMOVE_RE.search(text)
    if remove_match:
        ticker = remove_match.group(1).upper()
        return ChatResponse(
            message=f"Removing {ticker} from your watchlist.",
            watchlist_changes=[WatchlistChange(ticker=ticker, action="remove")],
        )

    add_match = _WATCHLIST_ADD_RE.search(text)
    if add_match:
        ticker = add_match.group(1).upper()
        return ChatResponse(
            message=f"Adding {ticker} to your watchlist.",
            watchlist_changes=[WatchlistChange(ticker=ticker, action="add")],
        )

    cash = portfolio_context.get("cash_balance")
    positions = portfolio_context.get("positions") or []
    total = portfolio_context.get("total_value")
    parts: list[str] = ["[mock] Portfolio summary:"]
    if cash is not None:
        parts.append(f"cash=${cash:,.2f}")
    if total is not None:
        parts.append(f"total=${total:,.2f}")
    parts.append(f"positions={len(positions)}")
    return ChatResponse(message=" ".join(parts))
