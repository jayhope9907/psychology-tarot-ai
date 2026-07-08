import os

from fastapi.testclient import TestClient

from app.main import PSYCHOLOGY_DATABASE, app


client = TestClient(app)


def setup_function():
    PSYCHOLOGY_DATABASE.clear()


def test_plan_controls_output_scope():
    response = client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-free",
            "user_story": "최근 업무 스트레스로 불안을 느끼고 있습니다.",
            "drawn_card": "The Hermit",
            "plan": "FREE",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == "FREE"
    assert len(body["output"]["actions"]) <= 2
    assert body["output"]["scope"] == "brief"
    profile = body["output"]["psychiatric_feature_profile"]["drawing_projective_profile"]
    assert profile["structural_sign"]
    assert profile["house_interpreted_code"]
    assert isinstance(profile["tree_energy_index"], (int, float))
    assert profile["person_relational_tag"]


def test_backoffice_samples_and_purge_work():
    create_response = client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-premium",
            "user_story": "관계 문제로 자존감이 흔들립니다.",
            "drawn_card": "The Lovers",
            "plan": "PREMIUM",
        },
    )
    assert create_response.status_code == 200

    samples_response = client.get("/api/v1/backoffice/samples")
    assert samples_response.status_code == 200
    assert len(samples_response.json()["samples"]) >= 1

    purge_response = client.delete(
        "/api/v1/therapy/purge",
        json={"user_id": "user-premium"},
    )
    assert purge_response.status_code == 200
    assert "user-premium" not in PSYCHOLOGY_DATABASE
