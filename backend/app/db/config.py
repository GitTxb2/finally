"""Database path configuration."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DB_PATH = "db/finally.db"


def get_db_path() -> Path:
    """Resolve the SQLite database path.

    Reads the DB_PATH environment variable, falling back to DEFAULT_DB_PATH
    for local development. The container sets DB_PATH=/app/db/finally.db
    so the file lands on the persistent volume mount.
    """
    raw = os.environ.get("DB_PATH", DEFAULT_DB_PATH)
    return Path(raw)
