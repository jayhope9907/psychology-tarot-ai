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


def test_archetype_mapping_recalibrates_profile():
    response = client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-archetype",
            "user_story": "최근 관계에서 상실감을 느끼고, 실수에 대한 두려움이 큽니다.",
            "drawn_card": "The Fool",
            "selected_cards": ["The Fool", "The Tower"],
            "plan": "PREMIUM",
        },
    )
    assert response.status_code == 200
    profile = response.json()["output"]["psychiatric_feature_profile"]
    assert profile["cognitive_distortion_flags"]
    assert profile["attachment_matrix_score"] >= 0.0
    assert profile["attachment_matrix_score"] <= 1.0
    assert profile["archetype_profiles"][0]["card_name"] == "The Fool"


def test_dashboard_returns_premium_trend_analysis():
    client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-dashboard",
            "user_story": "최근 업무 스트레스로 불안을 느끼고 있습니다.",
            "drawn_card": "The Hermit",
            "plan": "PREMIUM",
            "selected_cards": ["The Fool"],
        },
    )
    client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-dashboard",
            "user_story": "이제 조금 더 안정감을 찾고 있고 관계를 정리해보려 합니다.",
            "drawn_card": "The Magician",
            "plan": "PREMIUM",
            "selected_cards": ["The Magician"],
        },
    )

    response = client.get(
        "/api/v1/therapy/dashboard/user-dashboard",
        params={"membership_tier": "PREMIUM"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["membership_tier"] == "PREMIUM"
    assert body["history_length"] == 2
    assert body["trend_analysis"]["psychological_readiness_index"]["delta"] != 0.0
    assert "premium" in body["premium_therapeutic_summary"].lower()


def test_dashboard_returns_non_premium_summary_for_empty_history():
    response = client.get("/api/v1/therapy/dashboard/empty-user")
    assert response.status_code == 200
    body = response.json()
    assert body["history_length"] == 0
    assert body["summary"] == "Advanced analytics require a premium subscription."


def test_clinical_school_switching_tails_behavior_metadata():
    default_response = client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-school-default",
            "user_story": "최근 관계에서 불안을 느끼고 있습니다.",
            "drawn_card": "The Lovers",
            "plan": "PREMIUM",
        },
    )
    assert default_response.status_code == 200
    default_payload = default_response.json()["output"]
    assert default_payload["clinical_protocol_mode"] == "ROGERIAN"
    assert any("regard" in rule.lower() for rule in default_payload["assistant_behavior_rules"])

    cbt_response = client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-school-cbt",
            "user_story": "자기비난이 심해지고 실수를 과장해 생각합니다.",
            "drawn_card": "The Magician",
            "plan": "PREMIUM",
            "preferred_school": "BECK_CBT",
        },
    )
    assert cbt_response.status_code == 200
    cbt_payload = cbt_response.json()["output"]
    assert cbt_payload["clinical_protocol_mode"] == "BECK_CBT"
    assert any("cognitive" in rule.lower() or "thought" in rule.lower() for rule in cbt_payload["assistant_behavior_rules"])
    assert "thought" in cbt_payload["daily_logotherapy_homework_style"].lower()

    freudian_response = client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-school-freud",
            "user_story": "과거 경험이 현재 관계에 반복적으로 영향을 미칩니다.",
            "drawn_card": "The Fool",
            "plan": "PREMIUM",
            "preferred_school": "FREUDIAN",
        },
    )
    assert freudian_response.status_code == 200
    freud_payload = freudian_response.json()["output"]
    assert freud_payload["clinical_protocol_mode"] == "FREUDIAN"
    assert any("unconscious" in rule.lower() or "conflict" in rule.lower() for rule in freud_payload["assistant_behavior_rules"])
    assert "reflection" in freud_payload["daily_logotherapy_homework_style"].lower()


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

    purge_response = client.request(
        "DELETE",
        "/api/v1/therapy/purge",
        json={"user_id": "user-premium"},
    )
    assert purge_response.status_code == 200
    assert "user-premium" not in PSYCHOLOGY_DATABASE
