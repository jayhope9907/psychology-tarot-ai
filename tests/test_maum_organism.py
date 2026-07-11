from fastapi.testclient import TestClient

from app.main import app
from app.services.maum_organism import (
    build_organism_state,
    emit_activity,
    sync_after_checkin,
    sync_after_tarot_draw,
)

client = TestClient(app)


def test_organism_api_returns_web_structure():
    uid = "organism-test-user"
    response = client.get(f"/api/v1/organism/{uid}")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "organism"
    assert len(data["nodes"]) == 5
    assert len(data["edges"]) >= 5
    assert "next_actions" in data
    assert data["storage_keys"]["session_id"] == "psychology_ai_session_id"


def test_checkin_syncs_to_timeline_and_profile():
    uid = "organism-checkin-user"
    checkin = client.post(
        "/api/v1/checkin",
        json={"user_id": uid, "mood_score": 4, "note": "테스트"},
    ).json()
    sync_after_checkin(uid, checkin)
    state = build_organism_state(uid)
    assert state["dashboard"]["today_checkin"] is True
    assert any(t["feature"] == "checkin" for t in state["threads"])


def test_tarot_pick_syncs_organism():
    uid = "organism-tarot-user"
    deck = client.get("/api/v1/tarot/deck").json()
    ids = [deck["cards"][0]["id"], deck["cards"][1]["id"], deck["cards"][2]["id"]]
    draw = client.post(
        "/api/v1/tarot/pick",
        json={"user_id": uid, "spread": "three_card", "card_ids": ids},
    ).json()
    sync_after_tarot_draw(uid, draw, draw_id=1)
    state = build_organism_state(uid)
    assert state["dashboard"]["recent_tarot_count"] >= 1
    pulse = {n["id"]: n["pulse"] for n in state["nodes"]}
    assert pulse["tarot"] > 0.2


def test_emit_activity_records_feature():
    uid = "organism-emit-user"
    emit_activity(uid, "picto_chat", {"picto_ids": ["talk_yes"]}, source_id="test:1")
    state = build_organism_state(uid)
    assert any(t["feature"] == "picto" for t in state["threads"])
