import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_unified_clinical_catalog_api():
    res = client.get("/api/v1/clinical/catalog")
    assert res.status_code == 200
    data = res.json()
    assert data["counts"]["formal_instruments"] >= 14
    assert data["counts"]["projective_instruments"] == 6
    assert data["counts"]["total_items"] >= 50
    assert len(data["tracks"]) == 2
    assert len(data["formal_instruments"]) >= 14


def test_clinical_summary_api():
    res = client.get("/api/v1/clinical/summary/clinical-test-user")
    assert res.status_code == 200
    body = res.json()
    assert "counts" in body
    assert "overall" in body


def test_clinical_ui_route():
    res = client.get("/clinical")
    assert res.status_code == 200
    assert "마음 돌보기" in res.text or "알아가는" in res.text


def test_app_health_lists_clinical():
    res = client.get("/health")
    assert res.status_code == 200
    urls = res.json().get("urls") or {}
    assert "clinical" in urls
