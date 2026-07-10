import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.chat_session import ChatSessionState
from app.services.counseling_phase import PHASE_ASSESSMENT_BRIEFING, PHASE_RAPPORT
from app.services.daily_routine import record_checkin
from app.services.mood_assistant import (
    build_assessment_briefing_reply,
    build_mood_mandatory_system_block,
    get_mood_welcome_message,
    mood_priority_reply,
    rapport_ready_for_assessment,
    resolve_mood_context,
    should_nudge_assessment,
)

client = TestClient(app)


def test_resolve_mood_context_without_checkin():
    ctx = resolve_mood_context("mood-unknown-user")
    assert ctx.has_checkin is False
    assert ctx.score == 3


def test_resolve_mood_context_with_checkin():
    user = "mood-checkin-user"
    record_checkin(user, 2, "너무 힘들어요")
    ctx = resolve_mood_context(user)
    assert ctx.has_checkin is True
    assert ctx.score == 2
    assert ctx.note == "너무 힘들어요"


def test_mood_welcome_low_mood():
    user = "mood-welcome-low"
    record_checkin(user, 1, "우울해요")
    ctx = resolve_mood_context(user)
    welcome = get_mood_welcome_message(ctx)
    assert "1/5" in welcome
    assert "천천히" in welcome or "힘드" in welcome


def test_mood_system_block_forbids_payment_on_low_mood():
    user = "mood-system-low"
    record_checkin(user, 1)
    ctx = resolve_mood_context(user)
    state = ChatSessionState(user_id=user, counseling_phase=PHASE_RAPPORT)
    block = build_mood_mandatory_system_block(ctx, state)
    assert "결제" in block
    assert "공감" in block or "위로" in block


def test_rapport_ready_delays_assessment_for_low_mood():
    user = "mood-rapport-delay"
    record_checkin(user, 1)
    ctx = resolve_mood_context(user)
    state = ChatSessionState(user_id=user, counseling_phase=PHASE_RAPPORT)
    state.turn_count = 2
    assert rapport_ready_for_assessment(state, ctx) is False
    state.turn_count = 4
    assert rapport_ready_for_assessment(state, ctx) is True


def test_mood_priority_reply_first_turn():
    user = "mood-priority"
    record_checkin(user, 2, "답답해요")
    ctx = resolve_mood_context(user)
    state = ChatSessionState(user_id=user, counseling_phase=PHASE_RAPPORT)
    state.turn_count = 1
    reply = mood_priority_reply(ctx, state, "안녕하세요")
    assert reply is not None
    assert "2/5" in reply


def test_should_nudge_assessment_after_enough_turns():
    user = "mood-nudge"
    record_checkin(user, 3)
    ctx = resolve_mood_context(user)
    state = ChatSessionState(user_id=user, counseling_phase=PHASE_RAPPORT)
    state.turn_count = 2
    assert should_nudge_assessment(state, ctx) is False
    state.turn_count = 3
    assert should_nudge_assessment(state, ctx) is True


def test_assessment_briefing_reply_includes_payment_frame():
    user = "mood-briefing"
    record_checkin(user, 2)
    ctx = resolve_mood_context(user)
    package = {
        "tier_label": "핵심 패키지",
        "price_label": "9,900원",
        "mood_intro": "오늘 마음이 무거울 때는 짧은 검사가 도움이 돼요.",
        "mood_payment_copy": "부담 없는 핵심 패키지부터 시작할 수 있어요.",
    }
    reply = build_assessment_briefing_reply(ctx, package)
    assert "핵심 패키지" in reply
    assert "9,900원" in reply
    assert "부담" in reply


def test_mood_context_api():
    user = "mood-api-user"
    record_checkin(user, 4, "괜찮아요")
    response = client.get(f"/api/v1/chat/mood-context/{user}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["mood"]["score"] == 4
    assert payload["welcome_message"]
    assert "4/5" in payload["welcome_message"]
