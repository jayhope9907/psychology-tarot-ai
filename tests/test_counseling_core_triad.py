"""Rogers · Jung · CBT triad + empathic silence / multimodal tone."""
from __future__ import annotations

import pytest

from app.services.chat_session import ChatSessionState
from app.services.counseling_core_triad import (
    build_core_triad_directive,
    empathic_silence_ms,
    multimodal_tone_hint,
)
from app.services.chat_stream import build_chat_messages, run_chat_turn


def test_triad_directive_has_rogers_and_cbt():
    text = build_core_triad_directive(tarot_active=False)
    assert "로저스" in text
    assert "CBT" in text
    assert "동시성" not in text


def test_triad_directive_jung_when_tarot_active():
    text = build_core_triad_directive(tarot_active=True)
    assert "원형" in text
    assert "동시성" in text


def test_empathic_silence_scales_with_length_and_distress():
    short = empathic_silence_ms("안녕", distress=False)
    long = empathic_silence_ms("요즘 카드 결과가 너무 나빠서 연애운이 완전히 망한 것 같고 우울해요." * 3, distress=True)
    assert 400 <= short <= 2400
    assert long >= short
    assert long <= 2400


def test_multimodal_tone_hint():
    hint = multimodal_tone_hint({"mood_color": "blue", "mood_weather": "rain", "voice_cue": "low"})
    assert "멀티모달" in hint
    assert "차분" in hint or "천천히" in hint


def test_presence_wait_event_emitted():
    import asyncio

    state = ChatSessionState(session_id="triad-test", user_id="u-triad")

    async def fake_stream(*_args, **_kwargs):
        yield "마음이 "
        yield "닿아요."

    async def collect():
        events = []
        async for event in run_chat_turn(
            state,
            "카드 결과가 너무 나빠서 우울해요",
            client=None,
            stream_fn=fake_stream,
            multimodal_meta={"mood_color": "gray", "mood_weather": "cloud"},
        ):
            events.append(event)
        return events

    events = asyncio.run(collect())
    assert events[0]["event"] == "presence_wait"
    assert events[0]["data"]["ms"] >= 400
    assert "정리" in events[0]["data"]["label_ko"] or "헤아리" in events[0]["data"]["label_ko"]


def test_build_chat_messages_includes_triad_and_tone():
    state = ChatSessionState(session_id="triad-msg", user_id="u-triad")
    state.tarot_handoff = {"cards": [{"name": "Tower"}]}
    messages = build_chat_messages(
        state,
        "연애운이 완전히 망했구나",
        multimodal_meta={"mood_color": "red", "mood_weather": "storm"},
    )
    system = messages[0]["content"]
    assert "로저스" in system or "무조건" in system
    assert "CBT" in system or "재구성" in system
    assert "원형" in system or "투사" in system
    assert "멀티모달" in system
