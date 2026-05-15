"""LLM integration subsystem for FinAlly.

Public API:
    chat                - Main entry point; calls LLM (or mock) and returns ChatResponse
    ChatResponse        - Structured response object (message + trades + watchlist_changes)
    Trade               - Single trade action requested by the LLM
    WatchlistChange     - Single watchlist add/remove requested by the LLM
    Msg                 - Conversation history message (role + content)
    LLMError            - Raised on malformed LLM responses or transport failures
    SYSTEM_PROMPT       - The FinAlly system prompt used for live calls
"""

from .client import chat
from .models import ChatResponse, LLMError, Msg, Trade, WatchlistChange
from .prompts import SYSTEM_PROMPT

__all__ = [
    "chat",
    "ChatResponse",
    "Trade",
    "WatchlistChange",
    "Msg",
    "LLMError",
    "SYSTEM_PROMPT",
]
