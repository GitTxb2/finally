"""Database layer for FinAlly.

Backed by SQLite via stdlib `sqlite3`. The schema is created lazily on the
first connection and seeded with a default user profile and watchlist.

Public surface (intended for backend-engineer and llm-engineer):

    from app.db import (
        # connection / config
        connect, get_db_path, ensure_initialized, reset_init_cache,
        DEFAULT_USER_ID, DEFAULT_CASH_BALANCE, DEFAULT_WATCHLIST,

        # users_profile
        UserProfile, get_profile, get_cash_balance,
        set_cash_balance, adjust_cash_balance,

        # watchlist
        WatchlistEntry, list_tickers, list_entries,
        add_ticker, remove_ticker, contains,

        # positions
        Position, get_position, list_positions, apply_buy, apply_sell,

        # trades
        Trade, record_trade, list_trades,

        # portfolio snapshots
        PortfolioSnapshot, record_snapshot, list_snapshots,

        # chat
        ChatMessage, record_message, list_messages,
    )

Submodules are also importable directly (e.g. `from app.db import watchlist`)
if a caller wants the namespaced flavor.
"""

from . import chat, positions, snapshots, trades, users, watchlist
from .chat import ChatMessage, list_messages, record_message
from .config import get_db_path
from .connection import connect, reset_init_cache
from .positions import Position, apply_buy, apply_sell, get_position, list_positions
from .schema import (
    DEFAULT_CASH_BALANCE,
    DEFAULT_USER_ID,
    DEFAULT_WATCHLIST,
    ensure_initialized,
)
from .snapshots import PortfolioSnapshot, list_snapshots, record_snapshot
from .trades import Trade, list_trades, record_trade
from .users import UserProfile, adjust_cash_balance, get_cash_balance, get_profile, set_cash_balance
from .watchlist import (
    WatchlistEntry,
    add_ticker,
    contains,
    list_entries,
    list_tickers,
    remove_ticker,
)

__all__ = [
    # submodules
    "chat",
    "positions",
    "snapshots",
    "trades",
    "users",
    "watchlist",
    # connection / config
    "connect",
    "get_db_path",
    "ensure_initialized",
    "reset_init_cache",
    "DEFAULT_USER_ID",
    "DEFAULT_CASH_BALANCE",
    "DEFAULT_WATCHLIST",
    # users_profile
    "UserProfile",
    "get_profile",
    "get_cash_balance",
    "set_cash_balance",
    "adjust_cash_balance",
    # watchlist
    "WatchlistEntry",
    "list_tickers",
    "list_entries",
    "add_ticker",
    "remove_ticker",
    "contains",
    # positions
    "Position",
    "get_position",
    "list_positions",
    "apply_buy",
    "apply_sell",
    # trades
    "Trade",
    "record_trade",
    "list_trades",
    # snapshots
    "PortfolioSnapshot",
    "record_snapshot",
    "list_snapshots",
    # chat
    "ChatMessage",
    "record_message",
    "list_messages",
]
