import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.legal_compliance import (
    build_crisis_reply,
    build_legal_system_block,
    detect_crisis,
    reframe_clinical_label,
)

client = TestClient(app)


def test_detect_crisis_positive():
    assert detect_crisis("요즘 너무 힘들어서 죽고 싶어요") is True
    assert detect_crisis("그냥 우울해요") is False


def test_crisis_reply_includes_hotlines():
    reply = build_crisis_reply()
    assert "1393" in reply
    assert "119" in reply
    assert "129" in reply
    assert "의료" in reply or "아닙" in reply


def test_legal_system_block_non_medical():
    block = build_legal_system_block()
    assert "웰니스" in block
    assert "진료" in block or "의료" in block
    assert "진단" in block


def test_legal_consent_api():
    res = client.get("/api/v1/legal/consent")
    assert res.status_code == 200
    data = res.json()
    assert data["service_type"] == "ai_wellness_self_reflection"
    assert len(data["acknowledgments"]) >= 3
    assert data["crisis_resources"]


def test_legal_scope_api():
    res = client.get("/api/v1/legal/scope")
    assert res.status_code == 200
    assert "summary" in res.json()


def test_app_ui_route():
    res = client.get("/")
    assert res.status_code == 200
    assert "마음쉼터" in res.text
    assert "app-shell" in res.text


def test_home_route_embed():
    res = client.get("/home")
    assert res.status_code == 200
    assert "체크인" in res.text or "마음" in res.text


def test_legal_page_route():
    res = client.get("/legal")
    assert res.status_code == 200
    assert "면책" in res.text or "disclaimer" in res.text


def test_reframe_clinical_label():
    assert "전문" in reframe_clinical_label("병원·상담이 필요한지")


def test_crisis_short_circuits_llm():
    import asyncio

    from app.services.chat_session import ChatSessionState, clear_sessions
    from app.services.chat_stream import run_chat_turn

    async def collect():
        clear_sessions()
        state = ChatSessionState(user_id="crisis-user", session_id="crisis-sess")
        events = []
        async for event in run_chat_turn(state, "자살하고 싶어요", client=None):
            events.append(event)
        return events

    events = asyncio.run(collect())
    assert any(e["event"] == "crisis" for e in events)
    done = next(e for e in events if e["event"] == "done")
    assert done["data"].get("crisis_mode") is True
    assert "1393" in done["data"]["assistant_message"]
