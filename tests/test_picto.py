import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app
from app.services.picto_vocabulary import (
    compose_picto_message,
    mood_dimensions_from_picto,
    offline_chat_reply,
    picto_card_reply,
    picto_catalog,
    picto_offline_bundle,
    suggest_reply_pictos,
)

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / "static" / "picto-catalog.bundle.json"

client = TestClient(app)


def test_picto_catalog_has_picture_only_structure():
    data = picto_catalog()
    assert data["mode"] == "picture_only"
    assert len(data["home_nav"]) == 5
    assert "nav_history" in data["home_nav"]
    assert "mood_happy" in data["mood_ids"]
    assert "mood_ok" in data["mood_ids"]
    assert any(item["id"] == "talk_yes" for item in data["items"])


def test_compose_picto_message_joins_phrases():
    text = compose_picto_message(["talk_yes", "talk_thanks"])
    assert "[그림 대화]" in text
    assert "네·좋아요" in text
    assert "고마워요" in text


def test_mood_dimensions_from_picto():
    dims = mood_dimensions_from_picto("mood_scared")
    assert dims is not None
    assert dims["anxiety"] == 5


def test_suggest_reply_pictos_matches_keywords():
    pictos = suggest_reply_pictos("천천히 쉬어도 괜찮아요", limit=3)
    ids = [p["id"] for p in pictos]
    assert "talk_want_quiet" in ids or "mood_calm" in ids


def test_picto_card_reply():
    payload = picto_card_reply("card_sun")
    assert "밝" in payload["reply_text"]
    assert len(payload["reply_pictos"]) >= 1


def test_picto_ui_route():
    response = client.get("/picto")
    assert response.status_code == 200
    assert "picto-btn" in response.text
    assert "telModal" in response.text
    assert "floatDock" in response.text


def test_picto_catalog_api():
    response = client.get("/api/v1/picto/catalog")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "picture_only"
    assert len(data["talk_ids"]) >= 10


def test_picto_full_catalog_api():
    response = client.get("/api/v1/picto/catalog?full=1")
    assert response.status_code == 200
    data = response.json()
    assert data["bundle_version"] == 1
    assert len(data["items"]) >= 40
    assert "card_replies" in data
    assert "offline_chat_templates" in data


def test_picto_offline_bundle_file_matches_api():
    assert BUNDLE_PATH.exists(), "Run scripts/build_picto_bundle.py to generate offline bundle"
    file_data = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
    api_data = picto_offline_bundle()
    assert len(file_data["items"]) == len(api_data["items"])
    assert file_data["talk_ids"] == api_data["talk_ids"]
    assert file_data["card_ids"] == api_data["card_ids"]


def test_offline_chat_reply_templates():
    payload = offline_chat_reply(["talk_help_me"])
    assert payload["offline"] is True
    assert "1393" in payload["reply_text"]
    assert len(payload["reply_pictos"]) >= 1


def test_static_bundle_served():
    response = client.get("/static/picto-catalog.bundle.json")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 40


def test_picto_checkin_records_dimensions():
    response = client.post(
        "/api/v1/picto/checkin",
        json={"user_id": "picto-user-1", "mood_picto_id": "mood_happy"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mood_picto_id"] == "mood_happy"
    assert body["checkin"]["mood_score"] >= 1


def test_picto_card_api():
    response = client.post(
        "/api/v1/picto/card",
        json={"user_id": "picto-user-2", "card_picto_id": "card_star"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["emoji"] == "⭐"
    assert body["reply_pictos"]


def test_picto_chat_api(monkeypatch):
    async def fake_run_chat_turn(state, user_message, client, max_tokens=180, **kwargs):
        yield {"event": "token", "data": {"content": "괜찮아요. "}}
        yield {
            "event": "done",
            "data": {"session_id": state.session_id, "assistant_message": "괜찮아요. 함께 있어요."},
        }

    monkeypatch.setattr(main_module, "run_chat_turn", fake_run_chat_turn)
    monkeypatch.setattr(main_module, "sync_after_counseling", lambda uid, session: {})

    response = client.post(
        "/api/v1/picto/chat",
        json={"user_id": "picto-user-3", "picto_ids": ["talk_want_hug", "talk_yes"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert "안아주세요" in body["user_message"]
    assert body["reply_text"]
    assert len(body["reply_pictos"]) >= 1
    assert body["session_id"]


def test_infer_mood_picto_from_checkin_note():
    from app.services.picto_vocabulary import infer_mood_picto_from_checkin

    picto = infer_mood_picto_from_checkin({"note": "[그림기분] 😊 기쁨·좋아요", "mood_score": 5})
    assert picto["mood_picto_id"] == "mood_happy"
    assert picto["emoji"] == "😊"


def test_picto_mood_timeline_api():
    client.post(
        "/api/v1/picto/checkin",
        json={"user_id": "picto-timeline-user", "mood_picto_id": "mood_calm"},
    )
    response = client.get("/api/v1/picto/mood-timeline/picto-timeline-user")
    assert response.status_code == 200
    body = response.json()
    assert body["timeline"]
    assert body["timeline"][0]["emoji"] == "😌"


def test_picto_caregiver_alert_api():
    response = client.post(
        "/api/v1/picto/caregiver-alert",
        json={"user_id": "picto-care-user", "picto_ids": ["help_caregiver"]},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "recorded"
