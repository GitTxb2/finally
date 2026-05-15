"""Test fixtures for the db package.

Each test runs against its own temp SQLite file. The `DB_PATH` env var is
swapped to that file and the connection module's init cache is cleared so
lazy initialization runs fresh.
"""

from __future__ import annotations

import pytest

from app.db import connection as db_connection


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Point DB_PATH at a per-test SQLite file and reset the init cache."""
    path = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(path))
    db_connection.reset_init_cache()
    yield path
    db_connection.reset_init_cache()
