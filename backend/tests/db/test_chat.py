"""Tests for the chat_messages repository."""

from __future__ import annotations

import pytest

from app.db import list_messages, record_message


class TestChatMessages:
    def test_no_messages_initially(self, db_path):
        assert list_messages() == []

    def test_record_user_message(self, db_path):
        msg = record_message("user", "hello")
        assert msg.role == "user"
        assert msg.content == "hello"
        assert msg.actions is None

    def test_record_assistant_with_actions(self, db_path):
        actions = {
            "trades": [{"ticker": "AAPL", "side": "buy", "quantity": 10}],
            "watchlist_changes": [{"ticker": "PYPL", "action": "add"}],
        }
        msg = record_message("assistant", "Done.", actions=actions)
        assert msg.role == "assistant"
        assert msg.actions == actions

    def test_actions_roundtrip_through_db(self, db_path):
        actions = {"trades": [{"ticker": "AAPL", "side": "sell", "quantity": 2}]}
        record_message("assistant", "Sold.", actions=actions)
        msgs = list_messages()
        assert msgs[0].actions == actions

    def test_record_message_rejects_bad_role(self, db_path):
        with pytest.raises(ValueError):
            record_message("system", "you are a bot")  # type: ignore[arg-type]

    def test_list_messages_chronological(self, db_path):
        record_message("user", "first")
        record_message("assistant", "second")
        record_message("user", "third")
        contents = [m.content for m in list_messages()]
        assert contents == ["first", "second", "third"]

    def test_list_messages_with_limit_returns_recent_in_order(self, db_path):
        for i in range(5):
            record_message("user", f"m{i}")
        msgs = list_messages(limit=3)
        contents = [m.content for m in msgs]
        # most recent 3, still in chronological order
        assert contents == ["m2", "m3", "m4"]
