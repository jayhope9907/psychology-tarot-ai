"""Product line separation — consumer vs license vs disability."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_product_surfaces_api():
    res = client.get("/api/v1/product/surfaces")
    assert res.status_code == 200
    data = res.json()
    assert data["consumer_open"] is True
    ids = [line["id"] for line in data["lines"]]
    assert ids == ["consumer", "license", "disability"]
    consumer = next(l for l in data["lines"] if l["id"] == "consumer")
    routes = {r["route"] for r in consumer["routes"]}
    assert "/home" in routes
    assert "/picto" not in routes
    license = next(l for l in data["lines"] if l["id"] == "license")
    assert any(r["route"] == "/theories" for r in license["routes"])
    disability = next(l for l in data["lines"] if l["id"] == "disability")
    assert disability["preview_route"] == "/disability/picto"


def test_health_includes_product_lines():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert "product_lines" in body
    assert "학회 라이선스" in body["share_links"]
    assert "장애인용(보관)" in body["share_links"]
    assert "그림 마음" not in body["share_links"]


def test_theories_license_gate_without_key():
    res = client.get("/theories")
    assert res.status_code == 200
    assert "licenseGate" in res.text
    assert "라이선스 전용" in res.text


def test_expressive_license_gate_without_key():
    res = client.get("/expressive")
    assert res.status_code == 200
    assert "licenseGate" in res.text
