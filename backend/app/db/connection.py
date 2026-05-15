"""SQLite connection management.

Threading model: every caller opens a fresh connection via the `connect()`
context manager. SQLite connections are not safe to share across threads,
and FastAPI's default executor runs sync handlers on a thread pool, so a
new connection per scope is the simplest correct choice. Connections are
short-lived; the cost is negligible for SQLite. WAL mode lets readers and
the writer coexist.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .config import get_db_path
from .schema import ensure_initialized

_INIT_LOCK_PATHS: set[str] = set()


def _apply_pragmas(conn: sqlite3.Connection) -> None:
    """Apply session pragmas that must be set on every connection."""
    conn.execute("PRAGMA foreign_keys = ON")
    # journal_mode is persistent once set on the database, but issuing it
    # here is cheap and ensures WAL even if a stale rollback journal exists.
    conn.execute("PRAGMA journal_mode = WAL")


def _open(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        str(path),
        detect_types=sqlite3.PARSE_DECLTYPES,
        isolation_level=None,  # autocommit; we manage transactions explicitly
    )
    conn.row_factory = sqlite3.Row
    _apply_pragmas(conn)
    return conn


@contextmanager
def connect(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Yield a fresh SQLite connection with pragmas applied.

    Lazily creates and seeds the schema on first use for the given path.
    The connection is closed when the context exits.
    """
    path = db_path or get_db_path()
    conn = _open(path)
    try:
        key = str(path.resolve())
        if key not in _INIT_LOCK_PATHS:
            ensure_initialized(conn)
            _INIT_LOCK_PATHS.add(key)
        yield conn
    finally:
        conn.close()


def reset_init_cache() -> None:
    """Forget which DB paths have been initialized.

    Tests use this between cases that swap the underlying file.
    """
    _INIT_LOCK_PATHS.clear()
