import pytest
from fastapi.testclient import TestClient

from app.assessments.projective_battery import PROJECTIVE_INSTRUMENTS, projective_battery_catalog
from app.main import app
from app.services.picture_assessment import picture_assessment_catalog
from app.services.projective_scoring import score_drawing_meta, score_text_themes


client = TestClient(app)


def test_projective_catalog_has_six_clinical_instruments():
    catalog = projective_battery_catalog()
    assert catalog["mode"] == "clinical_projective"
    assert catalog["instrument_count"] == 6
    assert set(PROJECTIVE_INSTRUMENTS.keys()) == {"htp", "dap", "kfd", "rorschach", "tat", "sct"}
    assert catalog["total_items"] >= 17


def test_projective_items_have_stimuli_or_drawing():
    catalog = projective_battery_catalog()
    for form in catalog["instruments"]:
        for item in form["items"]:
            rt = item["response_type"]
            if rt == "inkblot" or rt == "tat_story":
                assert item.get("stimulus_url"), f"{item['item_id']} needs stimulus"
            if rt == "drawing":
                assert item.get("follow_up")


def test_picture_assessment_catalog_api():
    res = client.get("/api/v1/picture-assessment/catalog")
    assert res.status_code == 200
    data = res.json()
    assert data["instrument_count"] == 6
    assert "disclaimer" in data


def test_projective_submit_drawing_and_inkblot():
    start = client.post("/api/v1/picture-assessment/start", json={"user_id": "proj-user-1"})
    assert start.status_code == 200
    session_id = start.json()["session_id"]

    draw = client.post(
        "/api/v1/picture-assessment/submit",
        json={
            "user_id": "proj-user-1",
            "session_id": session_id,
            "instrument": "htp",
            "item_id": "htp_house",
            "drawing_data": "data:image/png;base64,abc",
            "meta": {"stroke_count": 12, "has_strokes": True, "canvas_width": 480, "canvas_height": 360, "bbox_width": 100, "bbox_height": 80},
            "association": "안전한 집 같아요",
        },
    )
    assert draw.status_code == 200
    assert draw.json()["recorded"]["recorded"] is True

    ink = client.post(
        "/api/v1/picture-assessment/submit",
        json={
            "user_id": "proj-user-1",
            "session_id": session_id,
            "instrument": "rorschach",
            "item_id": "rorschach_01",
            "association": "나비와 두 사람이 보여요",
        },
    )
    assert ink.status_code == 200

    results = client.get(f"/api/v1/picture-assessment/results/{session_id}")
    assert results.status_code == 200
    body = results.json()
    assert body["answered_items"] >= 2
    assert "projective_scores" in body


def test_projective_scoring_themes():
    themes = score_text_themes("요즘 불안하고 외로워요")
    assert themes.get("anxiety", 0) > 0
    assert themes.get("dependency", 0) > 0 or themes.get("isolation", 0) > 0


def test_drawing_meta_size_hint():
    meta = score_drawing_meta({"stroke_count": 5, "bbox_width": 20, "bbox_height": 15, "canvas_width": 400, "canvas_height": 400, "has_strokes": True})
    assert "size_hint" in meta


def test_picture_assessment_ui_route():
    res = client.get("/picture-assessment")
    assert res.status_code == 200
    assert "투영검사" in res.text
