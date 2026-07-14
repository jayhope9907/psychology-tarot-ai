"""Addiction wellness theory corpus + routing smoke tests."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.models.clinical import ClinicalSchool
from app.services.addiction_theories import ADDICTION_THEORIES, addiction_corpus
from app.services.counseling_theories import THEORY_CATALOG, THEORY_CATEGORIES
from app.services.persona_router import route_clinical_persona
from app.services.research_export import INVENTION_IDS
from app.services.user_agent_algorithm import extract_message_themes

client = TestClient(app)


def test_addiction_schools_in_catalog():
    assert "substance_addiction" in THEORY_CATEGORIES
    for school in ADDICTION_THEORIES:
        assert school in THEORY_CATALOG
        meta = THEORY_CATALOG[school]
        assert meta["techniques"]
        assert meta["directive"]
        assert "의료" in meta["directive"] or "전문" in meta["directive"]


def test_router_picks_addiction_cbt_for_substance_message():
    routed = route_clinical_persona("요즘 술·담배를 끊으려다 또 마셨어요. 중독인 것 같아요.", None, [])
    assert routed["school"] in {
        ClinicalSchool.ADDICTION_CBT,
        ClinicalSchool.RELAPSE_PREVENTION,
        ClinicalSchool.MOTIVATIONAL,
        ClinicalSchool.HARM_REDUCTION,
        ClinicalSchool.CRAVING_MINDFULNESS,
    }


def test_fingerprint_substance_theme():
    themes = extract_message_themes("술 갈망이 세고 재발이 걱정돼요")
    assert "substance" in themes


def test_addiction_corpus_api():
    res = client.get("/api/v1/addiction/corpus")
    assert res.status_code == 200
    data = res.json()
    assert data["theory_count"] >= 10
    assert data["technique_count"] >= 8
    assert "1332" in str(data.get("clinical_handoff"))


def test_theories_corpus_includes_addiction_block():
    res = client.get("/api/v1/theories/corpus")
    assert res.status_code == 200
    data = res.json()
    assert "addiction" in data
    assert data["addiction"]["theory_count"] >= 10


def test_invention_ids_include_fingerprint_and_addiction():
    ids = {item["id"] for item in INVENTION_IDS}
    assert {"INV-06", "INV-07", "INV-08"} <= ids


def test_addiction_corpus_helper():
    corp = addiction_corpus()
    assert corp["corpus_id"].startswith("substance")
    assert any(t["school"] == "RELAPSE_PREVENTION" for t in corp["theories"])
