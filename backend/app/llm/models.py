"""Pydantic models for LLM structured outputs and conversation history."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Trade(BaseModel):
    """A single trade action the LLM wants to execute."""

    ticker: str = Field(description="Ticker symbol, e.g. 'AAPL'")
    side: Literal["buy", "sell"]
    quantity: float = Field(gt=0, description="Number of shares (fractional allowed)")


class WatchlistChange(BaseModel):
    """A single watchlist add/remove the LLM wants to perform."""

    ticker: str = Field(description="Ticker symbol, e.g. 'PYPL'")
    action: Literal["add", "remove"]


class ChatResponse(BaseModel):
    """The structured response returned by the LLM (and by chat())."""

    message: str = Field(description="Conversational reply shown to the user")
    trades: list[Trade] = Field(default_factory=list)
    watchlist_changes: list[WatchlistChange] = Field(default_factory=list)


class Msg(BaseModel):
    """A single message in conversation history."""

    role: Literal["user", "assistant", "system"]
    content: str


class LLMError(RuntimeError):
    """Raised when the LLM call fails or returns a malformed response."""
