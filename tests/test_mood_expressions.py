from app.services.daily_routine import record_checkin, today_checkin
from app.services.mood_expressions import (
    CATEGORY_ORDER,
    MOOD_EXPRESSIONS,
    expression_deck_payload,
    infer_mood_from_expression,
)


def test_expression_deck_granular():
    deck = expression_deck_payload()
    assert deck["version"] == "1.0"
    assert deck["total"] >= 30
    assert set(CATEGORY_ORDER).issubset(set(deck["categories"]))
    ids = {e["id"] for e in deck["expressions"]}
    assert "tearful" in ids
    assert "anxious" in ids
    assert "masking" in ids
    assert "beaming" in ids


def test_infer_mood_from_anxious_expression():
    inferred = infer_mood_from_expression("anxious")
    assert inferred["inferred"] is True
    assert inferred["dimensions"]["anxiety"] >= 4
    assert inferred["mood_score"] <= 3
    assert "불안" in inferred["guess_ko"] or "불안" in inferred["label_ko"]


def test_infer_mood_from_beaming_expression():
    inferred = infer_mood_from_expression("beaming")
    assert inferred["dimensions"]["valence"] == 5
    assert inferred["mood_score"] >= 4


def test_record_checkin_from_expression_only():
    user = "expr-checkin-user"
    result = record_checkin(user, expression_id="tearful")
    assert result["expression_id"] == "tearful"
    assert result["expression"]["emoji"]
    assert result["dimensions"]["valence"] <= 2
    assert today_checkin(user)["expression_id"] == "tearful"


def test_checkin_api_expression_id():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    user = "expr-api-user"
    res = client.post(
        "/api/v1/checkin",
        json={"user_id": user, "expression_id": "worried", "note": "시험"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["expression_id"] == "worried"
    assert data["expression"]["guess_ko"]
    assert data["dimensions"]["anxiety"] >= 4


def test_mood_expressions_endpoint():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    res = client.get("/api/v1/mood/expressions")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == len(MOOD_EXPRESSIONS)
    assert len(data["expressions"]) >= 30


def test_dashboard_includes_mood_expressions():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    user = "expr-dash-user"
    client.post("/api/v1/checkin", json={"user_id": user, "expression_id": "soft_calm"})
    res = client.get(f"/api/v1/dashboard/{user}")
    assert res.status_code == 200
    data = res.json()
    assert data["mood_expressions"]["total"] >= 30
    assert data["today_checkin"]["expression_id"] == "soft_calm"
