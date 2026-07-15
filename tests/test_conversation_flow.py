import asyncio

import pytest

from app.services.assessment_package import complete_checkout
from app.services.chat_session import ChatSessionState, clear_sessions
from app.services.chat_stream import enrich_assistant_reply, fallback_reply, run_chat_turn
from app.services.orchestrator import decide_turn


@pytest.fixture(autouse=True)
def reset():
    clear_sessions()
    yield
    clear_sessions()


def test_depression_first_message_stays_in_rapport_without_payment():
    state = ChatSessionState(user_id="depression-flow")
    state.turn_count = 1

    decision = decide_turn(state, "지금 제가 우울증이 있어요")

    assert decision.action == "chat_only"
    assert state.counseling_phase == "rapport"


def test_depression_after_payment_triggers_phq9():
    state = ChatSessionState(user_id="depression-paid")
    state.turn_count = 3
    state.counseling_phase = "assessment"
    state.assessment_paid = True
    state.phase_notes = {"chief_complaint": "지금 제가 우울증이 있어요"}
    state.messages = [{"role": "user", "content": "지금 제가 우울증이 있어요"}]

    decision = decide_turn(state, "검사 시작해 주세요")

    assert decision.action == "inject_assessment"
    assert decision.assessment["instrument"] in {"phq9", "micro_emotion", "panas_mood"}


def test_assessment_request_triggers_injection():
    state = ChatSessionState(user_id="assessment-flow")
    state.turn_count = 3
    state.counseling_phase = "assessment"
    state.assessment_paid = True
    state.messages = [
        {"role": "user", "content": "지금 제가 우울증이 있어요"},
        {"role": "assistant", "content": "많이 힘드시겠어요."},
        {"role": "user", "content": "마음이 답답해요"},
        {"role": "assistant", "content": "답답한 마음이 느껴져요."},
    ]

    decision = decide_turn(state, "검사가능한가요?")

    assert decision.action == "inject_assessment"
    assert decision.reason == "user_requested_assessment"


def test_fallback_acknowledges_assessment_request():
    state = ChatSessionState(user_id="fallback-assessment")
    state.counseling_phase = "assessment_briefing"
    state.phase_notes = {"chief_complaint": "우울증이 있어요"}
    text = fallback_reply("검사가능한가요?", state)
    assert "검사" in text or "패키지" in text or "안내" in text


def test_fallback_with_injection_mentions_screening():
    state = ChatSessionState(user_id="fallback-inject")
    state.counseling_phase = "assessment"
    state.assessment_paid = True
    decision = decide_turn(state, "검사가능한가요?")
    text = fallback_reply("검사가능한가요?", state, decision)
    assert "검사" in text
    assert "PHQ" in text or "우울" in text or "스크리닝" in text


def test_relationship_message_selects_attachment():
    state = ChatSessionState(user_id="relation-flow")
    state.turn_count = 4
    state.counseling_phase = "assessment"
    state.assessment_paid = True
    state.messages = [
        {"role": "user", "content": "우울증이 있어요"},
        {"role": "assistant", "content": "힘드시겠어요"},
    ]

    decision = decide_turn(state, "대인관계죠")

    assert decision.action == "inject_assessment"
    assert decision.assessment["instrument"] in {"attachment_ecr", "phq9", "psychodynamic", "micro_emotion"}


def test_full_conversation_simulation():
    async def fake_stream(messages, max_tokens, client, assessment_response=None):
        yield "테스트 응답"

    async def run_flow():
        state = ChatSessionState(user_id="full-flow")
        events_log = []

        messages = [
            "지금 제가 우울증이 있어요",
            "최근 회사에서 일상이 힘들고 밤에 잠도 못 자요",
            "며칠째 불안하고 집중도 안 돼요. 회사에서 특히 버거워요",
        ]
        for message in messages:
            async for event in run_chat_turn(
                state,
                message,
                client=None,
                stream_fn=fake_stream,
            ):
                events_log.append((message, event["event"], event.get("data")))

        complete_checkout(state)

        for message in ["검사가능한가요?", "대인관계죠"]:
            async for event in run_chat_turn(
                state,
                message,
                client=None,
                stream_fn=fake_stream,
            ):
                events_log.append((message, event["event"], event.get("data")))

        return events_log

    events_log = asyncio.run(run_flow())
    assessment_events = [e for e in events_log if e[1] == "assessment"]

    assert len(assessment_events) >= 1
    first_assessment_turn = assessment_events[0][0]
    # Rapport 후 distress 턴(3턴+) 또는 명시적 검사 요청에서 첫 검사가 주입될 수 있음
    assert first_assessment_turn in {
        "며칠째 불안하고 집중도 안 돼요. 회사에서 특히 버거워요",
        "검사가능한가요?",
    }

    request_done = next(
        data
        for msg, evt, data in events_log
        if evt == "done" and msg == "검사가능한가요?"
    )
    first_reply = request_done.get("assistant_message") or ""
    # 검사 요청 턴에는 스트림 멘트가 나와도 assessment 이벤트로 주입됐는지로 충분
    request_assessments = [e for e in assessment_events if e[0] == "검사가능한가요?"]
    assert request_assessments or any(
        token in first_reply for token in ("가능", "검사", "스크리닝", "PHQ", "문항")
    )


def test_conceptualization_short_follow_up_not_repeat():
    state = ChatSessionState(user_id="work-repeat")
    state.counseling_phase = "conceptualization"
    state.phase_notes = {
        "chief_complaint": "오늘 직장에서 힘들었어요",
        "conceptualization_intro_done": True,
    }
    state.messages = [
        {"role": "user", "content": "힘들어요"},
        {"role": "assistant", "content": "오늘 직장에서 힘드셨군요."},
        {"role": "user", "content": "오늘 직장에서 힘들었어요"},
        {
            "role": "assistant",
            "content": (
                "지금까지 이야기해 주신 '오늘 직장에서 힘들었어요' 부분을 "
                "돌아보면, 비슷한 패턴이 반복되는 것 같아요. "
                "그때 가장 크게 느껴지는 감정이나 생각이 있다면 함께 짚어볼까요?"
            ),
        },
    ]

    reply = fallback_reply("네 맞아요 직장에서", state)

    assert "비슷한 패턴" not in reply
    assert "직장" in reply
    assert "어떤 일" in reply or "구체적" in reply


def test_enrich_assistant_reply_replaces_duplicate():
    state = ChatSessionState(user_id="dup-enrich")
    state.counseling_phase = "conceptualization"
    state.phase_notes = {
        "chief_complaint": "오늘 직장에서 힘들었어요",
        "conceptualization_intro_done": True,
    }
    duplicate = (
        "지금까지 이야기해 주신 '오늘 직장에서 힘들었어요' 부분을 "
        "돌아보면, 비슷한 패턴이 반복되는 것 같아요. "
        "그때 가장 크게 느껴지는 감정이나 생각이 있다면 함께 짚어볼까요?"
    )
    state.messages = [{"role": "assistant", "content": duplicate}]

    reply = enrich_assistant_reply(duplicate, "네 맞아요 직장에서", state)

    assert reply != duplicate
    assert "비슷한 패턴" not in reply
