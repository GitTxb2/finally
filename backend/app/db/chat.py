"""Repository functions for chat_messages."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any, Literal

from .connection import connect
from .schema import DEFAULT_USER_ID, now_iso

ChatRole = Literal["user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    id: str
    user_id: str
    role: ChatRole
    content: str
    actions: dict | list | None
    created_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "actions": self.actions,
            "created_at": self.created_at,
        }


def _row_to_message(row) -> ChatMessage:
    raw_actions = row["actions"]
    parsed_actions: Any = None
    if raw_actions:
        parsed_actions = json.loads(raw_actions)
    return ChatMessage(
        id=row["id"],
        user_id=row["user_id"],
        role=row["role"],
        content=row["content"],
        actions=parsed_actions,
        created_at=row["created_at"],
    )


def record_message(
    role: ChatRole,
    content: str,
    actions: dict | list | None = None,
    user_id: str = DEFAULT_USER_ID,
) -> ChatMessage:
    """Append a chat message to the log.

    `actions` is JSON-encoded (or stored as NULL when None). It is intended
    for assistant messages that include trades/watchlist changes executed
    by the LLM, but is permitted on any role.
    """
    if role not in ("user", "assistant"):
        raise ValueError(f"role must be 'user' or 'assistant', got {role!r}")
    msg_id = str(uuid.uuid4())
    ts = now_iso()
    actions_json = json.dumps(actions) if actions is not None else None
    with connect() as conn:
        conn.execute(
            "INSERT INTO chat_messages (id, user_id, role, content, actions, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (msg_id, user_id, role, content, actions_json, ts),
        )
    return ChatMessage(
        id=msg_id,
        user_id=user_id,
        role=role,
        content=content,
        actions=actions,
        created_at=ts,
    )


def list_messages(
    user_id: str = DEFAULT_USER_ID, limit: int | None = None
) -> list[ChatMessage]:
    """Return chat messages in chronological order (oldest first).

    When `limit` is set, returns the most recent `limit` messages but still
    in oldest-first order — useful for passing recent history to the LLM.
    """
    if limit is not None:
        query = (
            "SELECT id, user_id, role, content, actions, created_at FROM ("
            "  SELECT id, user_id, role, content, actions, created_at FROM chat_messages "
            "  WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT ?"
            ") ORDER BY created_at ASC, id ASC"
        )
        params: list = [user_id, limit]
    else:
        query = (
            "SELECT id, user_id, role, content, actions, created_at FROM chat_messages "
            "WHERE user_id = ? ORDER BY created_at ASC, id ASC"
        )
        params = [user_id]
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
        return [_row_to_message(row) for row in rows]
