from app.services.stress_management import (
    build_stress_management_plan,
    build_stress_management_reply,
    should_trigger_stress_management,
)
from app.services.chat_session import ChatSessionState


def test_should_trigger_stress_keywords():
    assert should_trigger_stress_management("요즘 스트레스 받아요")
    assert should_trigger_stress_management("너무 긴장돼요")
    assert not should_trigger_stress_management("오늘 날씨가 좋아요")


def test_stress_plan_has_protocol():
    plan = build_stress_management_plan(
        clinical_setup={"resistance_level": "HIGH", "cognitive_level": "SIMPLE_EASY"},
        pre_sud=7.0,
    )
    assert plan["protocolId"] == "stress_3min_reset"
    assert plan["durationMin"] == 3
    assert plan["homeworkType"] == "grounding_log"
    assert plan["clinicalAdaptiveSetup"]["adaptive_enabled"] is True


def test_stress_reply_simple_easy():
    state = ChatSessionState(user_id="u1", session_id="s1")
    state.cognitive_level = "SIMPLE_EASY"
    reply = build_stress_management_reply(state, "스트레스가 너무 심해요")
    assert "3분" in reply
    assert "숨 3번" in reply or "호흡" in reply


def test_stress_reply_deaf_emoji():
    state = ChatSessionState(user_id="u1", session_id="s1")
    reply = build_stress_management_reply(
        state,
        "압박감이 심해요",
        clinical_setup={"sensory_impairment_deaf": True},
    )
    assert "🌬" in reply or "👀" in reply
