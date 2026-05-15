"""Shared fixtures for API-level tests.

Each test gets a fresh app instance backed by a temporary SQLite database
and a temporary static directory, so tests are fully isolated from one
another and from the project-level `db/` directory.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import connection as db_connection


@pytest.fixture
def temp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Point the DB layer at a fresh SQLite file under tmp_path."""
    db_path = tmp_path / "finally.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    db_connection.reset_init_cache()
    yield db_path
    db_connection.reset_init_cache()


@pytest.fixture
def temp_static(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide a static directory with a placeholder index.html."""
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<!doctype html><title>FinAlly</title>")
    monkeypatch.setenv("STATIC_DIR", str(static_dir))
    return static_dir


@pytest.fixture
def client(temp_db: Path, temp_static: Path) -> Iterator[TestClient]:
    """A FastAPI TestClient with an isolated DB and static dir.

    Using TestClient as a context manager triggers the lifespan handler
    (market source start/stop), exercising the real startup path.
    """
    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c
