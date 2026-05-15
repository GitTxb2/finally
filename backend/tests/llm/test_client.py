"""Tests for the live-path LLM client wiring (with the network mocked).

These exercise message construction, response parsing, and malformed-response
handling without making real API calls.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.llm import chat
from app.llm.client import (
    EXTRA_BODY,
    MODEL,
    _build_messages,
    _extract_content,
    _parse_response,
)
from app.llm.models import ChatResponse, LLMError, Msg
from app.llm.prompts import SYSTEM_PROMPT


def _fake_response(content: str):
    """Build a minimal object that quacks like a LiteLLM ChatCompletion."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


@pytest.fixture
def live_env(monkeypatch):
    """Force the live path: LLM_MOCK off, OPENROUTER_API_KEY set."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("LLM_MOCK", raising=False)


class TestBuildMessages:
    def test_includes_system_prompt_and_context_and_user(self):
        msgs = _build_messages(
            SYSTEM_PROMPT,
            [],
            {"cash_balance": 5000.0},
            "hello",
        )
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == SYSTEM_PROMPT
        assert msgs[1]["role"] == "system"
        assert "cash_balance" in msgs[1]["content"]
        assert msgs[-1] == {"role": "user", "content": "hello"}

    def test_includes_history_in_order(self):
        history = [
            Msg(role="user", content="prev question"),
            Msg(role="assistant", content="prev answer"),
        ]
        msgs = _build_messages(SYSTEM_PROMPT, history, {}, "new question")
        roles = [m["role"] for m in msgs]
        # system, system(context), user(prev), assistant(prev), user(new)
        assert roles == ["system", "system", "user", "assistant", "user"]
        assert msgs[2]["content"] == "prev question"
        assert msgs[3]["content"] == "prev answer"
        assert msgs[4]["content"] == "new question"


class TestExtractContent:
    def test_extracts_string(self):
        assert _extract_content(_fake_response('{"message":"x"}')) == '{"message":"x"}'

    def test_empty_raises(self):
        with pytest.raises(LLMError):
            _extract_content(_fake_response(""))

    def test_whitespace_only_raises(self):
        with pytest.raises(LLMError):
            _extract_content(_fake_response("   \n  "))

    def test_no_choices_raises(self):
        with pytest.raises(LLMError):
            _extract_content(SimpleNamespace(choices=[]))

    def test_missing_message_raises(self):
        with pytest.raises(LLMError):
            _extract_content(SimpleNamespace(choices=[SimpleNamespace()]))


class TestParseResponse:
    def test_valid_response(self):
        resp = _parse_response('{"message": "ok", "trades": [], "watchlist_changes": []}')
        assert isinstance(resp, ChatResponse)
        assert resp.message == "ok"

    def test_valid_with_actions(self):
        raw = (
            '{"message": "buying", '
            '"trades":[{"ticker":"AAPL","side":"buy","quantity":10}],'
            '"watchlist_changes":[]}'
        )
        resp = _parse_response(raw)
        assert resp.trades[0].ticker == "AAPL"

    def test_not_json_raises_llmerror(self):
        with pytest.raises(LLMError) as exc_info:
            _parse_response("this is not json at all")
        assert "not valid JSON" in str(exc_info.value)

    def test_partial_json_raises_llmerror(self):
        with pytest.raises(LLMError):
            _parse_response('{"message": "ok"')

    def test_wrong_schema_raises_llmerror(self):
        # Missing required `message` field.
        with pytest.raises(LLMError) as exc_info:
            _parse_response('{"trades": []}')
        assert "schema" in str(exc_info.value).lower() or "ChatResponse" in str(exc_info.value)

    def test_wrong_enum_raises_llmerror(self):
        raw = '{"message":"x","trades":[{"ticker":"AAPL","side":"hold","quantity":1}]}'
        with pytest.raises(LLMError):
            _parse_response(raw)


class TestChatLivePath:
    def test_calls_completion_with_expected_args(self, live_env, monkeypatch):
        captured = {}

        def fake_completion(**kwargs):
            captured.update(kwargs)
            return _fake_response('{"message": "hi", "trades": [], "watchlist_changes": []}')

        import litellm

        monkeypatch.setattr(litellm, "completion", fake_completion)

        resp = chat(
            history=[Msg(role="user", content="earlier")],
            portfolio_context={"cash_balance": 1000.0},
            user_message="how am I doing?",
        )

        assert isinstance(resp, ChatResponse)
        assert resp.message == "hi"
        assert captured["model"] == MODEL
        assert captured["extra_body"] == EXTRA_BODY
        assert captured["response_format"] is ChatResponse
        assert captured["reasoning_effort"] == "low"
        roles = [m["role"] for m in captured["messages"]]
        assert roles[0] == "system"
        assert roles[-1] == "user"
        assert captured["messages"][-1]["content"] == "how am I doing?"

    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("LLM_MOCK", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        with pytest.raises(LLMError):
            chat(portfolio_context={}, user_message="hi")

    def test_completion_failure_wrapped_as_llmerror(self, live_env, monkeypatch):
        def boom(**kwargs):
            raise RuntimeError("network exploded")

        import litellm

        monkeypatch.setattr(litellm, "completion", boom)

        with pytest.raises(LLMError) as exc_info:
            chat(portfolio_context={}, user_message="hi")
        assert "network exploded" in str(exc_info.value)

    def test_malformed_completion_response_raises(self, live_env, monkeypatch):
        def fake_completion(**kwargs):
            return _fake_response("not json")

        import litellm

        monkeypatch.setattr(litellm, "completion", fake_completion)

        with pytest.raises(LLMError):
            chat(portfolio_context={}, user_message="hi")

    def test_custom_system_prompt_overrides_default(self, live_env, monkeypatch):
        captured = {}

        def fake_completion(**kwargs):
            captured.update(kwargs)
            return _fake_response('{"message": "ok"}')

        import litellm

        monkeypatch.setattr(litellm, "completion", fake_completion)

        chat(
            system_prompt="custom system",
            portfolio_context={},
            user_message="hello",
        )
        assert captured["messages"][0]["content"] == "custom system"
