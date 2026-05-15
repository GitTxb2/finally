"""Tests for the portfolio_snapshots repository."""

from __future__ import annotations

from app.db import list_snapshots, record_snapshot


class TestSnapshots:
    def test_no_snapshots_initially(self, db_path):
        assert list_snapshots() == []

    def test_record_snapshot(self, db_path):
        snap = record_snapshot(10000.0)
        assert snap.total_value == 10000.0
        assert snap.recorded_at
        assert snap.id

    def test_list_snapshots_chronological(self, db_path):
        record_snapshot(10000.0)
        record_snapshot(10100.0)
        record_snapshot(10250.0)
        values = [s.total_value for s in list_snapshots()]
        assert values == [10000.0, 10100.0, 10250.0]

    def test_list_snapshots_with_limit(self, db_path):
        for v in (10000.0, 10100.0, 10250.0, 10300.0):
            record_snapshot(v)
        snaps = list_snapshots(limit=2)
        assert len(snaps) == 2
