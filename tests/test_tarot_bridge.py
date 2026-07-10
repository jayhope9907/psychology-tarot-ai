from fastapi.testclient import TestClient

from app.main import app
from app.services.chat_session import ChatSessionState, clear_sessions
from app.services.tarot import draw_cards
from app.services.tarot_bridge import (
    apply_tarot_handoff,
    build_counselor_bridge_message,
    build_tarot_handoff,
    build_tarot_system_block,
    should_suggest_tarot,
)


client = TestClient(app)


def setup_function():
    clear_sessions()


def test_build_tarot_handoff():
    draw = draw_cards(count=3, spread="three_card", seed=3)
    reading = {"summary": "테스트 요약", "ai_analysis": "분석", "cbt_actions": ["행동1"]}
    handoff = build_tarot_handoff("직장이 힘들어요", draw, reading)
    assert handoff["user_story"] == "직장이 힘들어요"
    assert len(handoff["cards"]) == 3
    assert handoff["bridge_message"]


def test_apply_tarot_handoff_to_session():
    state = ChatSessionState(user_id="blend-user")
    draw = draw_cards(count=1, spread="single", seed=8)
    reading = {"summary": "요약", "psychology_themes": ["자기효능감"]}
    handoff = build_tarot_handoff("불안해요", draw, reading)
    result = apply_tarot_handoff(state, handoff)
    assert result["session_id"] == state.session_id
    assert state.tarot_blended is True
    assert state.phase_notes.get("chief_complaint") == "불안해요"
    assert "타로" in build_tarot_system_block(state) or "카드" in build_tarot_system_block(state)


def test_should_suggest_tarot_in_conceptualization():
    state = ChatSessionState(user_id="suggest-user")
    state.counseling_phase = "conceptualization"
    state.turn_count = 4
    assert should_suggest_tarot(state) is True
    state.tarot_blended = True
    assert should_suggest_tarot(state) is False


def test_tarot_bridge_endpoint():
    draw = draw_cards(count=2, spread="three_card", seed=2)
    reading = {
        "summary": "카드 요약",
        "ai_analysis": "심리 분석",
        "cards": [],
        "cbt_actions": ["호흡하기"],
    }
    response = client.post(
        "/api/v1/tarot/bridge",
        json={
            "user_id": "bridge-user",
            "user_story": "관계가 힘들어요",
            "draw": draw,
            "reading": reading,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["bridge_message"]
    assert payload["session_id"]


def test_counselor_bridge_message_mentions_cards():
    cards = [
        {
            "position": "현재",
            "name_ko": "탑",
            "orientation": "정방향",
            "psychology_theme": "위기 속 재구성",
        }
    ]
    msg = build_counselor_bridge_message("힘들어요", cards, {"summary": "요약"})
    assert "탑" in msg
    assert "타로" in msg
