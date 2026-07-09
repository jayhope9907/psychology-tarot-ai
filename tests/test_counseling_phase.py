import asyncio

import pytest

from app.services.chat_session import ChatSessionState, clear_sessions
from app.services.chat_stream import run_chat_turn
from app.services.counseling_phase import (
    PHASE_ASSESSMENT,
    PHASE_ASSESSMENT_BRIEFING,
    PHASE_CONCEPTUALIZATION,
    PHASE_INTERVENTION,
    PHASE_RAPPORT,
    PHASE_TERMINATION,
    phase_allows_assessment,
    sync_counseling_phase,
)
from app.services.orchestrator import decide_turn


@pytest.fixture(autouse=True)
def reset():
    clear_sessions()
    yield
    clear_sessions()


def test_depression_advances_to_briefing_after_rapport():
    state = ChatSessionState(user_id="phase-depression")
    state.turn_count = 1
    sync_counseling_phase(state, "지금 제가 우울증이 있어요")
    assert state.counseling_phase == PHASE_RAPPORT

    state.turn_count = 2
    state.messages = [{"role": "user", "content": "최근 회사에서 우울하고 일상이 힘들어요"}]
    sync_counseling_phase(state, "밤에 잠도 못 자요")
    assert state.counseling_phase == PHASE_RAPPORT

    state.turn_count = 3
    state.messages.append({"role": "assistant", "content": "많이 힘드시겠어요"})
    info = sync_counseling_phase(state, "며칠째 불안하고 집중도 안 돼요. 회사에서 특히 버거워요")

    assert state.counseling_phase == PHASE_ASSESSMENT_BRIEFING
    assert info["phase_label"] == "검사 안내·결제"
    assert state.phase_notes.get("client_profile", {}).get("substantive_user_turns", 0) >= 2


def test_neutral_greeting_stays_in_rapport():
    state = ChatSessionState(user_id="phase-greeting")
    state.turn_count = 1

    sync_counseling_phase(state, "안녕하세요")

    assert state.counseling_phase == PHASE_RAPPORT
    assert not phase_allows_assessment(state, "안녕하세요")


def test_assessment_phase_allows_screening_when_paid():
    state = ChatSessionState(user_id="phase-screen")
    state.counseling_phase = PHASE_ASSESSMENT
    state.assessment_paid = True
    state.turn_count = 3

    assert phase_allows_assessment(state, "요즘 힘들어요")


def test_intervention_phase_blocks_screening_without_request():
    state = ChatSessionState(user_id="phase-intervention")
    state.counseling_phase = PHASE_INTERVENTION
    state.assessment_paid = True
    state.turn_count = 12

    assert not phase_allows_assessment(state, "요즘 힘들어요")
    assert phase_allows_assessment(state, "검사 가능한가요?")


def test_completed_assessments_move_to_conceptualization():
    state = ChatSessionState(user_id="phase-concept")
    state.counseling_phase = PHASE_ASSESSMENT
    state.assessment_paid = True
    state.turn_count = 6
    state.assessments_completed = 2
    state.formal_answers = {"phq9": {"phq9_q1": 2, "phq9_q2": 1}}

    sync_counseling_phase(state, "그 패턴이 반복되는 것 같아요")

    assert state.counseling_phase == PHASE_CONCEPTUALIZATION


def test_intervention_ready_moves_from_conceptualization():
    state = ChatSessionState(user_id="phase-ready")
    state.counseling_phase = PHASE_CONCEPTUALIZATION
    state.turn_count = 10
    state.phase_notes = {"chief_complaint": "대인관계가 힘들어요"}

    sync_counseling_phase(state, "어떻게 하면 좋을까요?")

    assert state.counseling_phase == PHASE_INTERVENTION
    assert state.phase_notes.get("goals")


def test_termination_signal():
    state = ChatSessionState(user_id="phase-end")
    state.counseling_phase = PHASE_INTERVENTION
    state.turn_count = 15

    sync_counseling_phase(state, "오늘은 여기까지 할게요, 고마워요")

    assert state.counseling_phase == PHASE_TERMINATION


def test_depression_injects_phq9_after_payment():
    state = ChatSessionState(user_id="phase-phq")
    state.turn_count = 3
    state.counseling_phase = PHASE_ASSESSMENT
    state.assessment_paid = True
    state.phase_notes = {"chief_complaint": "지금 제가 우울증이 있어요"}
    state.messages = [{"role": "user", "content": "지금 제가 우울증이 있어요"}]

    decision = decide_turn(state, "검사 시작해 주세요")

    assert decision.action == "inject_assessment"
    assert decision.assessment["instrument"] in {"phq9", "micro_emotion"}


def test_conversation_includes_phase_in_orchestrator_event():
    async def fake_stream(messages, max_tokens, client, assessment_response=None):
        yield "테스트 응답"

    async def run_flow():
        state = ChatSessionState(user_id="phase-sse")
        phase_events = []
        async for event in run_chat_turn(
            state,
            "지금 제가 우울증이 있어요",
            client=None,
            stream_fn=fake_stream,
        ):
            if event["event"] == "orchestrator":
                phase_events.append(event["data"].get("counseling_phase"))
            if event["event"] == "done":
                phase_events.append(event["data"].get("counseling_phase"))
        return phase_events

    phase_events = asyncio.run(run_flow())

    assert phase_events
    assert phase_events[0]["phase"] == PHASE_RAPPORT
