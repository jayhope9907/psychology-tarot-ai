import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app
from app.services.tarot import build_draw_from_picks, build_local_reading, draw_cards, get_major_arcana, list_deck_catalog


client = TestClient(app)


def test_tarot_rules_api_and_enrichment():
    response = client.get("/api/v1/tarot/rules")
    assert response.status_code == 200
    rules = response.json()
    assert rules["count"] == 3
    assert rules["reverse_chance"] == 0.5
    assert len(rules["practice_ko"]) >= 8
    assert "wands" in rules["suits"]

    draw = draw_cards(count=3, spread="three_card", seed=11)
    assert draw["rules"]["deck"]["total"] == 78
    for card in draw["cards"]:
        assert "orientation_rule" in card
        assert "arcana_rule" in card
        assert card.get("position_guide")


def test_tarot_reading_prompt_includes_suit_rules():
    from app.prompt_config import build_tarot_reading_system_prompt

    prompt = build_tarot_reading_system_prompt()
    assert "지팡이" in prompt or "수트" in prompt
    assert "3장" in prompt or "3카드" in prompt
    assert "역방향" in prompt


def test_tarot_deck_has_22_major_arcana():
    cards = get_major_arcana()
    assert len(cards) == 22
    assert cards[0]["name_en"] == "The Fool"


def test_tarot_full_deck_has_78_cards():
    from app.services.tarot import get_full_deck, get_minor_arcana

    assert len(get_minor_arcana()) == 56
    assert len(get_full_deck()) == 78


def test_list_deck_catalog_endpoint():
    response = client.get("/api/v1/tarot/deck")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["cards"]) == 78
    assert payload.get("total") == 78
    assert payload.get("major_count") == 22
    assert payload.get("minor_count") == 56
    assert "three_card" in payload["spreads"]
    assert payload["cards"][0]["image_url"].startswith("/api/v1/tarot/card-image/")
    assert "upright_ko" in payload["cards"][0]
    assert payload.get("ui", {}).get("show_hover_hints") is True
    minor = next(c for c in payload["cards"] if c.get("arcana") == "minor")
    assert minor["suit"] in ("wands", "cups", "swords", "pentacles")
    assert "/api/v1/tarot/card-image/" in minor["image_url"]


def test_deck_catalog_hides_meanings_on_render(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("TAROT_SHOW_HOVER_HINTS", raising=False)
    response = client.get("/api/v1/tarot/deck")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ui"]["show_hover_hints"] is False
    card = payload["cards"][0]
    assert card["psychology_theme"] == ""
    assert card["upright_ko"] == ""
    assert card["keywords_ko"] == []
    assert card["name_ko"] == ""
    assert card["id"]


def test_pick_endpoint_user_selected_minor_card():
    response = client.post(
        "/api/v1/tarot/pick",
        json={"spread": "three_card", "card_ids": ["fool", "wands_ace", "cups_three"]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["cards"]) == 3
    assert payload["cards"][1]["id"] == "wands_ace"
    assert payload["cards"][1]["image_url"].startswith("/api/v1/tarot/card-image/")


def test_pick_endpoint_user_selected_cards():
    response = client.post(
        "/api/v1/tarot/pick",
        json={"spread": "three_card", "card_ids": ["fool", "magician", "sun"]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["cards"]) == 3
    assert payload["cards"][0]["id"] == "fool"
    assert payload["cards"][0]["image_url"].startswith("/api/v1/tarot/card-image/")


def test_card_image_endpoint_serves_original(monkeypatch, tmp_path):
    from app.services import tarot as tarot_svc

    sample = tmp_path / "fool.jpg"
    sample.write_bytes(b"\xff\xd8\xff" + b"0" * 1200)

    monkeypatch.setattr(tarot_svc, "resolve_card_image_file", lambda card_id: sample if card_id == "fool" else None)
    response = client.get("/api/v1/tarot/card-image/fool")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")
    assert len(response.content) > 1000

    missing = client.get("/api/v1/tarot/card-image/not_a_card")
    assert missing.status_code == 404


def test_build_draw_from_picks():
    result = build_draw_from_picks(
        ["empress", "moon", "sun"], spread="three_card", reversed_flags=[False, True, False]
    )
    assert len(result["cards"]) == 3
    assert result["cards"][1]["reversed"] is True
    assert result["spread"] == "three_card"
    assert result["positions"] == ["과거·뿌리", "현재·핵심", "미래·방향"]


def test_draw_forces_three_card_even_if_single_requested():
    result = draw_cards(count=1, spread="single", seed=42)
    assert len(result["cards"]) == 3
    assert result["spread"] == "three_card"
    assert result["rules"]["reverse_chance"] == 0.5


def test_pick_rejects_non_three():
    response = client.post(
        "/api/v1/tarot/pick",
        json={"spread": "single", "card_ids": ["fool"]},
    )
    assert response.status_code == 400


def test_tarot_ui_is_three_card_only():
    response = client.get("/tarot")
    assert response.status_code == 200
    assert "원카드" not in response.text
    assert "3카드" in response.text
    assert "과거" in response.text


def test_draw_three_cards_with_positions():
    result = draw_cards(count=3, spread="three_card", seed=42)
    assert len(result["cards"]) == 3
    assert result["positions"] == ["과거·뿌리", "현재·핵심", "미래·방향"]
    for card in result["cards"]:
        assert card["name_ko"]
        assert "meaning_ko" in card


def test_draw_endpoint():
    response = client.post("/api/v1/tarot/draw", json={"count": 3, "spread": "three_card", "seed": 7})
    assert response.status_code == 200
    assert len(response.json()["cards"]) == 3


def test_tarot_ui_route():
    response = client.get("/tarot")
    assert response.status_code == 200
    assert "3D 타로" in response.text
    assert "카메라 커스텀" in response.text
    assert "camHeight" in response.text
    assert "원카드" not in response.text
    assert "3카드" in response.text
    assert "과거" in response.text
    assert "원카드" not in response.text


def test_psychometrics_hosts_mind_themes():
    from fastapi.testclient import TestClient
    from app.main import app

    ui = TestClient(app).get("/psychometrics")
    assert ui.status_code == 200
    assert "마음 주제" in ui.text
    assert "domainBar" in ui.text

    clinical = TestClient(app).get("/clinical")
    assert clinical.status_code == 200
    assert "마음 주제 · 심리검사" in clinical.text
    assert 'id="domainList"' not in clinical.text


def test_tarot_reading_endpoint_with_mock_openai(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="타로 심리 풀이 테스트입니다."))]
            )

    class FakeClient:
        def __init__(self):
            self.api_key = "test-key"
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(main_module, "client", FakeClient())

    draw = draw_cards(count=3, spread="three_card", seed=99)
    response = client.post(
        "/api/v1/tarot/reading",
        json={
            "user_story": "요즘 직장에서 힘들어요",
            "spread": "three_card",
            "count": 3,
            "cards": draw["cards"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["reading"]["summary"]
    assert payload["reading"]["cards"]
    assert "타로" in payload["reading"]["ai_analysis"] or payload["reading"]["ai_analysis"]


def test_local_reading_workplace_actions():
    draw = draw_cards(count=3, spread="three_card", seed=1)
    reading = build_local_reading("직장에서 스트레스가 심해요", draw)
    assert reading.get("reading_tone") == "three_card_classic"
    assert "3카드" in reading["summary"] or "과거" in reading["summary"]
    assert any("직장" in action for action in reading["cbt_actions"])


def test_tarot_reading_prompt_is_light_projection():
    from app.prompt_config import build_tarot_reading_system_prompt

    prompt = build_tarot_reading_system_prompt()
    assert "깊게" in prompt
    assert "그림자" in prompt
    assert "3장" in prompt or "3카드" in prompt
    assert "과거" in prompt
    assert "메이저" in prompt
    assert "역방향" in prompt


def test_archetype_map_covers_all_major_arcana():
    from app.services.tarot import TAROT_ARCHETYPE_MAP

    for card in get_major_arcana():
        assert card["name_en"] in TAROT_ARCHETYPE_MAP
