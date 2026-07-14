"""Instant keyword reaction + IP map tests."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.models.clinical import ClinicalSchool
from app.services.instant_keyword_router import react_instantly
from app.services.persona_router import route_clinical_persona
from app.services.platform_ip_map import build_platform_ip_map
from app.services.research_export import INVENTION_IDS

client = TestClient(app)


def test_instant_prefers_addiction_over_generic_hard():
    reaction = react_instantly("요즘 술 때문에 너무 힘들어요. 끊다가 또 마셨어요")
    assert reaction.school in {
        ClinicalSchool.ADDICTION_CBT,
        ClinicalSchool.RELAPSE_PREVENTION,
        ClinicalSchool.MOTIVATIONAL,
        ClinicalSchool.HARM_REDUCTION,
        ClinicalSchool.CRAVING_MINDFULNESS,
    }
    assert reaction.score > 0
    assert reaction.matched_keywords


def test_persona_router_exposes_instant_reaction():
    routed = route_clinical_persona("담배 갈망이 심해서 손이 가요", None, [])
    assert routed["instant_reaction"]["score"] > 0
    assert routed["school"] in {
        ClinicalSchool.ADDICTION_CBT,
        ClinicalSchool.CRAVING_MINDFULNESS,
        ClinicalSchool.RELAPSE_PREVENTION,
        ClinicalSchool.MOTIVATIONAL,
    }


def test_instant_route_api():
    res = client.get("/api/v1/chat/instant-route", params={"message": "재발이 걱정돼요 술"})
    assert res.status_code == 200
    data = res.json()["reaction"]
    assert data["school"]
    assert data["matched_keywords"] or data["features"]


def test_platform_ip_map_covers_all_inventions():
    payload = build_platform_ip_map()
    ids = {item["id"] for item in payload["inventions"]}
    assert {"INV-01", "INV-09", "INV-12"} <= ids
    assert payload["theory_count"] >= 40
    assert payload["addiction_theory_count"] >= 10


def test_invention_ids_reach_inv12():
    ids = {item["id"] for item in INVENTION_IDS}
    assert "INV-12" in ids


def test_platform_ip_api():
    res = client.get("/api/v1/research/platform-ip-map")
    assert res.status_code == 200
    assert res.json()["invention_count"] >= 12
