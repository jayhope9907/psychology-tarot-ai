from fastapi.testclient import TestClient

from app.main import app
from app.services.counseling_style import (
    build_style_system_block,
    normalize_style,
    resolve_counseling_style,
    search_voice_presets,
)
from app.services.persistence import get_user_settings, save_user_settings

client = TestClient(app)


def test_style_catalog_api():
    res = client.get("/api/v1/chat/style-catalog")
    assert res.status_code == 200
    data = res.json()
    assert len(data["counselors"]) >= 14
    assert len(data["voice_presets"]) >= 16
    assert len(data["textures"]) >= 5
    assert len(data["theories"]) >= 18


def test_save_and_load_counseling_style():
    user = "style-user-1"
    res = client.post(
        "/api/v1/settings/counseling-style",
        json={
            "user_id": user,
            "counselor_id": "minjun",
            "texture": "calm",
            "tone": {"warmth": 5, "formality": 2, "pace": 2, "directness": 2},
            "voice_preset_id": "male_minjun_warm",
            "voice_enabled": True,
            "auto_speak": True,
        },
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["counselor_name"] == "김민준"
    assert payload["counselor"]["gender"] == "male"
    assert payload["voice"]["id"] == "male_minjun_warm"

    get_res = client.get(f"/api/v1/settings/counseling-style/{user}")
    assert get_res.json()["counselor_id"] == "minjun"
    settings = get_user_settings(user)
    assert settings["counseling_style"]["auto_speak"] is True


def test_voice_preset_search():
    female = search_voice_presets(gender="female")
    assert all(p["gender"] == "female" for p in female)
    soft = search_voice_presets("부드")
    assert soft
    assert any("부드" in p["label"] or "부드" in " ".join(p.get("tags", [])) for p in soft)


def test_voice_presets_api():
    res = client.get("/api/v1/voice/presets", params={"gender": "male", "query": "깊"})
    assert res.status_code == 200
    data = res.json()
    assert data["tts_engine"] == "browser_speech_synthesis"
    assert isinstance(data["presets"], list)


def test_build_style_system_block_mentions_counselor():
    style = resolve_counseling_style({"counseling_style": normalize_style({"counselor_id": "jieun", "texture": "calm"})})
    block = build_style_system_block(style)
    assert "박지은" in block
    assert "질감" in block
