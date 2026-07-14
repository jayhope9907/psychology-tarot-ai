"""Multi-turn chat should not repeat the same assistant phrasing."""
from __future__ import annotations

import asyncio

import pytest

from app.services.chat_session import ChatSessionState, clear_sessions
from app.services.chat_stream import (
    _is_near_duplicate,
    _repeats_recent_assistant,
    enrich_assistant_reply,
    run_chat_turn,
)


@pytest.fixture(autouse=True)
def reset_sessions():
    clear_sessions()
    yield
    clear_sessions()


def test_near_duplicate_detects_similar_closing_question():
    a = "직장이 힘드시군요. 그때 몸이나 마음에서 가장 먼저 느껴진 반응은 무엇이었나요?"
    b = "상사 이야기 들었어요. 그때 몸이나 마음에서 가장 먼저 느껴진 반응은 무엇이었나요?"
    assert _is_near_duplicate(a, b) is True


def test_enrich_keeps_llm_when_user_message_is_reflected():
    state = ChatSessionState(user_id="enrich-keep")
    state.messages.append({"role": "assistant", "content": "첫 답변입니다."})
    user_message = "요즘 직장 때문에 많이 힘들어요"
    llm_text = f"말씀하신 '{user_message}' 부분이 마음에 남아요. 그때 어떤 감정이 컸나요?"
    result = enrich_assistant_reply(llm_text, user_message, state)
    assert result == llm_text


def test_enrich_swaps_near_duplicate_llm_output():
    state = ChatSessionState(user_id="enrich-swap")
    previous = "그때 몸이나 마음에서 가장 먼저 느껴진 반응은 무엇이었나요?"
    state.messages.append({"role": "assistant", "content": previous})
    user_message = "상사한테 계속 깨져서 자신감이 떨어져요"
    llm_text = "상사 이야기 들었어요. 그때 몸이나 마음에서 가장 먼저 느껴진 반응은 무엇이었나요?"
    result = enrich_assistant_reply(llm_text, user_message, state)
    assert result != llm_text
    assert not _repeats_recent_assistant(state, result)


def test_multi_turn_fake_llm_avoids_identical_assistant_messages():
    async def fake_stream(messages, max_tokens, client, assessment_response=None):
        user = messages[-1]["content"] if messages else ""
        if isinstance(user, list):
            user = " ".join(
                part.get("text", "") for part in user if isinstance(part, dict) and part.get("type") == "text"
            )
        snippet = (user or "")[:24]
        yield f"말씀하신 '{snippet}' 부분이 마음에 남아요. "
        yield "그때 몸이나 마음에서 가장 먼저 느껴진 반응은 무엇이었나요?"

    async def run_flow():
        state = ChatSessionState(user_id="repeat-flow")
        replies = []
        for message in [
            "요즘 직장 때문에 많이 힘들어요",
            "상사한테 계속 깨져서 자신감이 떨어져요",
            "네 맞아요 그래서 출근하기가 무서워요",
        ]:
            text = ""
            async for event in run_chat_turn(state, message, client=object(), stream_fn=fake_stream):
                if event["event"] == "done":
                    text = event["data"].get("assistant_message", "")
            replies.append(text)
        return replies

    replies = asyncio.run(run_flow())
    assert len(replies) == 3
    assert replies[0].strip() != replies[1].strip()
    assert all(reply.strip() for reply in replies)
