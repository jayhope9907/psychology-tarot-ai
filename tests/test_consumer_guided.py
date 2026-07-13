"""Consumer guided path on clinical catalog."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.consumer_guided import STARTER_INSTRUMENT_IDS, guided_catalog_slice


client = TestClient(app)


def test_guided_slice_prefers_starters():
    fake = [{"instrument_id": iid, "user_title": iid, "item_count": 2} for iid in STARTER_INSTRUMENT_IDS[:3]]
    fake.append({"instrument_id": "other", "user_title": "other", "item_count": 9})
    g = guided_catalog_slice(fake)
    assert g["starters"]
    assert all(s["instrument_id"] in STARTER_INSTRUMENT_IDS for s in g["starters"])


def test_catalog_exposes_guided():
    res = client.get("/api/v1/clinical/catalog")
    assert res.status_code == 200
    data = res.json()
    assert "guided" in data
    assert data["guided"]["starters"]
    assert "copy" in data["guided"]
