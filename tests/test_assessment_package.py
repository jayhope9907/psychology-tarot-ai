import asyncio

import pytest

from app.services.assessment_package import build_assessment_package, complete_checkout
from app.services.chat_session import ChatSessionState, clear_sessions
from app.services.chat_stream import run_chat_turn
from app.services.counseling_phase import PHASE_ASSESSMENT_BRIEFING, PHASE_RAPPORT
from app.services.orchestrator import decide_turn


@pytest.fixture(autouse=True)
def reset():
    clear_sessions()
    yield
    clear_sessions()


def test_build_package_includes_timeline_and_instruments():
    state = ChatSessionState(user_id="pkg-user")
    state.turn_count = 2
    state.phase_notes = {"chief_complaint": "우울증이 있고 마음이 답답해요"}

    package = build_assessment_package(state, "마음이 답답해요")

    assert package["total_instruments"] >= 3
    assert package["process_timeline"]
    assert package["instrument_steps"]
    assert package["price_krw"] > 0
    assert package.get("case_preview")
    assert package["case_preview"]["hypotheses"]
    assert package["case_preview"]["future_vision"]
    assert package["case_preview"]["defense_points"]
    assert "phq9" in {item["instrument_id"] for item in package["recommended_instruments"]}


def test_rapport_does_not_inject_assessment_without_payment():
    state = ChatSessionState(user_id="rapport-gate")
    state.turn_count = 1

    decision = decide_turn(state, "지금 제가 우울증이 있어요")

    assert state.counseling_phase == PHASE_RAPPORT
    assert decision.action == "chat_only"


def test_briefing_phase_shows_package_and_blocks_tests(monkeypatch):
    monkeypatch.setattr("app.services.consumer_access.consumer_open", lambda: False)
    state = ChatSessionState(user_id="briefing-gate")
    state.turn_count = 3
    state.messages = [
        {"role": "user", "content": "최근 회사에서 우울하고 일상이 힘들어요"},
        {"role": "assistant", "content": "많이 힘드시겠어요."},
        {"role": "user", "content": "밤에 잠도 못 자고 몇 달째 지속되고 있어요"},
    ]
    state.phase_notes = {
        "chief_complaint": "최근 회사에서 우울하고 일상이 힘들어요",
        "client_profile": {
            "chief_complaint": "최근 회사에서 우울하고 일상이 힘들어요",
            "emotional_themes": ["우울"],
            "context_themes": ["회사"],
            "impact_areas": ["일상", "잠"],
            "duration_hint": "몇달",
            "substantive_user_turns": 2,
        },
    }
    state.counseling_phase = PHASE_ASSESSMENT_BRIEFING

    decision = decide_turn(state, "검사 안내도 될까요?")

    assert state.counseling_phase == PHASE_ASSESSMENT_BRIEFING
    assert decision.action == "chat_only"
    assert decision.reason == "awaiting_payment"


def test_paid_session_allows_assessment_injection():
    state = ChatSessionState(user_id="paid-gate")
    state.turn_count = 3
    state.counseling_phase = "assessment"
    state.assessment_paid = True
    state.phase_notes = {"chief_complaint": "우울증이 있어요"}
    state.messages = [
        {"role": "user", "content": "지금 제가 우울증이 있어요"},
        {"role": "assistant", "content": "힘드시겠어요."},
    ]

    decision = decide_turn(state, "검사 시작해 주세요")

    assert decision.action == "inject_assessment"


def test_checkout_unlocks_assessment_phase():
    state = ChatSessionState(user_id="checkout-user")
    state.turn_count = 2
    state.counseling_phase = PHASE_ASSESSMENT_BRIEFING
    package = build_assessment_package(state, "우울증")
    state.assessment_package = package
    state.assessment_package_ready = True

    result = complete_checkout(state)

    assert result["success"] is True
    assert state.assessment_paid is True
    assert state.counseling_phase == "assessment"


def test_chat_emits_assessment_package_after_rapport():
    async def fake_stream(messages, max_tokens, client, assessment_response=None):
        yield "안내드릴게요."

    async def run_flow():
        state = ChatSessionState(user_id="pkg-sse")
        events = []
        async for event in run_chat_turn(state, "안녕하세요", client=None, stream_fn=fake_stream):
            events.append(event)
        async for event in run_chat_turn(
            state,
            "최근 회사에서 우울하고 일상이 힘들어요",
            client=None,
            stream_fn=fake_stream,
        ):
            events.append(event)
        async for event in run_chat_turn(
            state,
            "밤에 잠도 못 자고 몇 달째 불안해요. 회사에서 특히 버거워요",
            client=None,
            stream_fn=fake_stream,
        ):
            events.append(event)
        return events

    events = asyncio.run(run_flow())
    package_events = [e for e in events if e["event"] == "assessment_package"]

    assert package_events
    assert package_events[0]["data"]["instrument_steps"]
