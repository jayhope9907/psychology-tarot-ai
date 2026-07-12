from fastapi.testclient import TestClient

from app.main import app
from app.models.clinical import ClinicalSchool
from app.services.counseling_theories import THEORY_CATALOG
from app.services.scholars_catalog import ART_THERAPY_TECHNIQUES, SCHOLARS, scholars_corpus


client = TestClient(app)


def test_enum_and_catalog_aligned():
    assert set(THEORY_CATALOG.keys()) == set(ClinicalSchool)


def test_scholars_cover_art_therapy_founders():
    ids = {s["id"] for s in SCHOLARS}
    for needed in ("naumburg", "kramer", "cane", "malchiodi", "rubin", "mcniff", "hinz"):
        assert needed in ids
    assert len(ART_THERAPY_TECHNIQUES) >= 8


def test_scholars_corpus_api():
    res = client.get("/api/v1/theories/corpus")
    assert res.status_code == 200
    data = res.json()
    assert data["school_count"] >= 40
    assert data["scholar_count"] >= 60
    assert len(data["art_techniques"]) >= 8


def test_scholars_filter_by_school():
    res = client.get("/api/v1/scholars", params={"school": "ART_THERAPY"})
    assert res.status_code == 200
    body = res.json()
    assert all(s["school"] == "ART_THERAPY" for s in body["scholars"])
    assert len(body["scholars"]) >= 5


def test_theories_ui():
    res = client.get("/theories")
    assert res.status_code == 200
    assert "학자" in res.text


def test_scholars_corpus_helper():
    corpus = scholars_corpus()
    assert corpus["scholar_count"] == len(SCHOLARS)
