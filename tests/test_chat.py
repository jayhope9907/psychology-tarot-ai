import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.assessments.phq9 import PHQ9Instrument
from app.main import PSYCHOLOGY_DATABASE, app
from app.services.chat_session import CHAT_SESSIONS, ChatSessionState, clear_sessions, get_or_create_session
from app.services.fatigue_manager import compute_fatigue, should_block_new_assessment
from app.services.chat_stream import run_chat_turn
from app.services.orchestrator import decide_turn, record_assessment_answer, record_assessment_offer


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_chat_state():
    clear_sessions()
    PSYCHOLOGY_DATABASE.clear()
    yield
    clear_sessions()
    PSYCHOLOGY_DATABASE.clear()


def test_phq9_progressive_items_and_partial_score():
    instrument = PHQ9Instrument()
    answers = {"phq9_q1": 2, "phq9_q2": 1}
    score = instrument.score_partial(answers)

    assert instrument.next_item({}).item_id == "phq9_q1"
    assert instrument.next_item(answers).item_id == "phq9_q3"
    assert score["partial_score"] == 3
    assert score["completion_rate"] == 0.4


def test_fatigue_blocks_assessments_after_warmup_and_pending():
    state = ChatSessionState(user_id="user-fatigue")
    state.turn_count = 3
    state.assessments_offered = 2
    state.assessments_completed = 0
    state.pending_assessment = {"item_id": "phq9_q1"}

    assert should_block_new_assessment(state, "요즘 불안합니다") is True
    assert compute_fatigue(state, "요즘 불안합니다") >= 0.5


def test_orchestrator_injects_matched_assessment_after_distress_and_warmup():
    state = ChatSessionState(user_id="user-orchestrator")
    state.turn_count = 4
    state.counseling_phase = "assessment"
    state.assessment_paid = True

    decision = decide_turn(state, "요즘 우울하고 무기력해서 잠도 잘 못 자요.")

    assert decision.action == "inject_assessment"
    assert decision.assessment is not None
    assert decision.assessment["instrument"] == "phq9"
    assert decision.selection is not None


def test_orchestrator_respects_warmup_period():
    state = ChatSessionState(user_id="user-warmup")
    state.turn_count = 1

    decision = decide_turn(state, "안녕하세요, 처음 왔어요.")

    assert decision.action == "chat_only"
    assert decision.reason == "warmup"


def test_record_assessment_answer_updates_formal_progress():
    state = ChatSessionState(user_id="user-answer")
    record_assessment_offer(
        state,
        {
            "instrument": "phq9",
            "item_id": "phq9_q1",
            "prompt": "test",
            "response_type": "likert_0_3",
            "options": [],
        },
    )

    result = record_assessment_answer(
        state,
        {"instrument": "phq9", "item_id": "phq9_q1", "value": 2, "skipped": False},
    )

    assert result["recorded"] is True
    assert state.formal_answers["phq9"]["phq9_q1"] == 2
    assert state.assessments_completed == 1
    assert state.pending_assessment is None


def test_chat_stream_emits_orchestrator_assessment_and_done_events():
    async def fake_stream(messages, max_tokens, client, assessment_response=None):
        yield "안녕하세요. "
        yield "함께 이야기해요."

    async def collect_events():
        state = get_or_create_session("user-stream", plan="BASIC")
        state.turn_count = 4
        state.counseling_phase = "assessment"
        state.assessment_paid = True
        events = []
        async for event in run_chat_turn(
            state,
            "요즘 불안하고 우울해요.",
            client=None,
            max_tokens=120,
            stream_fn=fake_stream,
        ):
            events.append(event)
        return events

    import asyncio

    events = asyncio.run(collect_events())

    event_names = [event["event"] for event in events]
    assert "orchestrator" in event_names
    assert "token" in event_names
    assert "done" in event_names
    assert any(event["event"] == "assessment" for event in events)


def test_chat_stream_endpoint_returns_sse_payload(monkeypatch):
    async def fake_stream(messages, max_tokens, client, assessment_response=None):
        yield "스트리밍 응답"

    async def fake_run_chat_turn(state, user_message, client, max_tokens=320, assessment_response=None, stream_fn=None, preferred_school=None):
        yield {"event": "orchestrator", "data": {"action": "chat_only", "reason": "test", "fatigue": {"fatigue_score": 0.1}}}
        yield {"event": "token", "data": {"content": "스트리밍 응답"}}
        yield {
            "event": "done",
            "data": {
                "session_id": state.session_id,
                "assistant_message": "스트리밍 응답",
                "profile_delta": {"turn_count": 1, "fatigue": {"fatigue_score": 0.1}},
            },
        }

    monkeypatch.setattr(main_module, "run_chat_turn", fake_run_chat_turn)

    with client.stream(
        "POST",
        "/api/v1/chat/stream",
        json={"user_id": "user-endpoint", "message": "안녕하세요", "plan": "BASIC"},
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_lines())

    assert "event: token" in body
    assert "스트리밍 응답" in body
    assert "event: done" in body


def test_chat_ui_route_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "이서연" in response.text


def test_chat_session_state_endpoint():
    session = get_or_create_session("user-state", plan="BASIC")
    session.turn_count = 2

    response = client.get(f"/api/v1/chat/sessions/{session.session_id}")
    assert response.status_code == 200
    assert response.json()["turn_count"] == 2


def test_chat_turn_persists_profile_into_psychology_database():
    async def fake_stream(messages, max_tokens, client, assessment_response=None):
        yield "응답"

    async def run_turn():
        state = get_or_create_session("user-store", plan="BASIC")
        async for event in run_chat_turn(
            state,
            "오늘 기분이 좋아요.",
            client=None,
            stream_fn=fake_stream,
        ):
            if event["event"] == "done":
                main_module._store_chat_profile("user-store", event["data"]["profile_delta"], "BASIC")

    import asyncio

    asyncio.run(run_turn())
    assert "user-store" in PSYCHOLOGY_DATABASE
