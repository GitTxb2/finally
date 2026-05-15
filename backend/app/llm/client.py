"""LLM client: LiteLLM -> OpenRouter (Cerebras inference) with structured outputs.

The single public entry point is `chat()`. When env var `LLM_MOCK=true`, the
deterministic mock path in `app.llm.mock` is used instead of the network call.
"""

from __future__ import annotations

import json
import os
from typing import Any

from pydantic import ValidationError

from .mock import mock_chat
from .models import ChatResponse, LLMError, Msg
from .prompts import SYSTEM_PROMPT, build_portfolio_context_message

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}


def _is_mock_mode() -> bool:
    return os.getenv("LLM_MOCK", "").strip().lower() in {"1", "true", "yes", "on"}


def _build_messages(
    system_prompt: str,
    history: list[Msg],
    portfolio_context: dict[str, Any],
    user_message: str,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": build_portfolio_context_message(portfolio_context)},
    ]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})
    return messages


def _extract_content(response: Any) -> str:
    """Pull the assistant message string out of a LiteLLM ChatCompletion response."""
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        raise LLMError(f"LLM response has no choices[0].message.content: {exc}") from exc
    if not isinstance(content, str) or not content.strip():
        raise LLMError("LLM returned empty content")
    return content


def _parse_response(content: str) -> ChatResponse:
    try:
        return ChatResponse.model_validate_json(content)
    except ValidationError as exc:
        try:
            json.loads(content)
        except json.JSONDecodeError as json_exc:
            raise LLMError(
                f"LLM response was not valid JSON: {json_exc.msg}"
            ) from json_exc
        raise LLMError(f"LLM response did not match ChatResponse schema: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LLMError(f"LLM response was not valid JSON: {exc.msg}") from exc


def chat(
    system_prompt: str | None = None,
    history: list[Msg] | None = None,
    portfolio_context: dict[str, Any] | None = None,
    user_message: str = "",
) -> ChatResponse:
    """Send a chat turn to the LLM (or mock) and return a structured response.

    Args:
        system_prompt: Override the default FinAlly system prompt. Pass None to use SYSTEM_PROMPT.
        history: Prior conversation turns, in chronological order. Defaults to [].
        portfolio_context: Dict with the user's portfolio state (cash, positions, watchlist, etc.).
            Rendered into a system message for the model. Defaults to {}.
        user_message: The user's new message. Required.

    Returns:
        ChatResponse with `message`, `trades`, and `watchlist_changes`.

    Raises:
        LLMError: On transport failures, malformed responses, or empty user_message.
    """
    if not user_message or not user_message.strip():
        raise LLMError("user_message is required")

    sys_prompt = system_prompt if system_prompt is not None else SYSTEM_PROMPT
    hist = history or []
    ctx = portfolio_context or {}

    if _is_mock_mode():
        return mock_chat(user_message, ctx)

    if not os.getenv("OPENROUTER_API_KEY"):
        raise LLMError("OPENROUTER_API_KEY is not set (and LLM_MOCK is not enabled)")

    # Lazy import so mock-mode callers don't pay the litellm import cost.
    from litellm import completion

    messages = _build_messages(sys_prompt, hist, ctx, user_message)

    try:
        response = completion(
            model=MODEL,
            messages=messages,
            response_format=ChatResponse,
            reasoning_effort="low",
            extra_body=EXTRA_BODY,
        )
    except Exception as exc:  # litellm raises a variety of provider-specific errors
        raise LLMError(f"LLM call failed: {exc}") from exc

    content = _extract_content(response)
    return _parse_response(content)
