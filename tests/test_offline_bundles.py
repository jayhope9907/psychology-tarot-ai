import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.counsel_offline import counsel_offline_bundle, match_offline_counsel_reply
from app.services.tarot import list_deck_catalog

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]


def test_counsel_offline_bundle_api():
    response = client.get("/api/v1/counsel/offline-bundle")
    assert response.status_code == 200
    data = response.json()
    assert data["bundle_version"] == 1
    assert len(data["rules"]) >= 8


def test_match_offline_counsel_crisis():
    result = match_offline_counsel_reply("너무 힘들어서 죽고 싶어요")
    assert result["crisis"] is True
    assert "1393" in result["reply_text"]


def test_tarot_deck_bundle_file():
    path = ROOT / "static" / "tarot-deck.bundle.json"
    assert path.exists(), "Run scripts/build_offline_bundles.py"
    data = json.loads(path.read_text(encoding="utf-8"))
    api = list_deck_catalog()
    assert data["total"] == api["total"]
    assert len(data["cards"]) == 78


def test_tarot_deck_bundle_served():
    response = client.get("/static/tarot-deck.bundle.json")
    assert response.status_code == 200
    assert response.json()["total"] == 78


def test_counsel_offline_bundle_served():
    response = client.get("/static/counsel-offline.bundle.json")
    assert response.status_code == 200
    assert response.json()["mode"] == "offline_counseling"
