import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app
from app.services.tarot import build_local_reading, draw_cards, get_major_arcana, list_deck_catalog


client = TestClient(app)


def test_tarot_deck_has_22_major_arcana():
    cards = get_major_arcana()
    assert len(cards) == 22
    assert cards[0]["name_en"] == "The Fool"


def test_list_deck_catalog_endpoint():
    response = client.get("/api/v1/tarot/deck")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["cards"]) == 22
    assert "three_card" in payload["spreads"]


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

    draw = draw_cards(count=1, spread="single", seed=99)
    response = client.post(
        "/api/v1/tarot/reading",
        json={
            "user_story": "요즘 직장에서 힘들어요",
            "spread": "single",
            "count": 1,
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
    assert any("직장" in action for action in reading["cbt_actions"])


def test_archetype_map_covers_all_major_arcana():
    from app.services.tarot import TAROT_ARCHETYPE_MAP

    for card in get_major_arcana():
        assert card["name_en"] in TAROT_ARCHETYPE_MAP
