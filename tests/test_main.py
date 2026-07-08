import json
import os
from types import SimpleNamespace

from fastapi.testclient import TestClient

import app.main as main_module
from app.main import ANALYTICS_CACHE, DASHBOARD_CACHE, PSYCHOLOGY_DATABASE, PURGED_USERS, ClinicalSchool, app


client = TestClient(app)


def setup_function():
    PSYCHOLOGY_DATABASE.clear()
    PURGED_USERS.clear()
    DASHBOARD_CACHE.invalidate()
    ANALYTICS_CACHE.invalidate()


def test_prompt_binding_factory_adjusts_prompt_variables_per_school():
    freudian_binding = main_module.PromptContextWeightBindingFactory(
        school=ClinicalSchool.FREUDIAN,
        psychological_readiness_index=0.2,
        cognitive_distortions=["all_or_nothing", "catastrophizing"],
    ).build()
    assert freudian_binding["weights"]["interpretation_depth"] >= 0.7
    assert "심층 해석" in freudian_binding["system_prompt"]

    rogerian_binding = main_module.PromptContextWeightBindingFactory(
        school=ClinicalSchool.ROGERIAN,
        psychological_readiness_index=0.3,
        cognitive_distortions=["rumination"],
    ).build()
    assert rogerian_binding["weights"]["empathy_level"] >= 0.7
    assert "공감 수준" in rogerian_binding["system_prompt"]

    cbt_binding = main_module.PromptContextWeightBindingFactory(
        school=ClinicalSchool.BECK_CBT,
        psychological_readiness_index=0.4,
        cognitive_distortions=["all_or_nothing", "overgeneralization"],
    ).build()
    assert cbt_binding["weights"]["homework_structure"] >= 0.7
    assert "인지 재구성 과제" in cbt_binding["system_prompt"]


def test_consultation_pipeline_injects_dynamic_prompt_context(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="dynamic prompt ok"))])

    class FakeClient:
        def __init__(self):
            self.api_key = "test-key"
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(main_module, "client", FakeClient())

    response = client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-prompt-binding",
            "user_story": "실패를 반복하면 나는 실패자라고 느낍니다.",
            "drawn_card": "The Tower",
            "plan": "PREMIUM",
            "preferred_school": "BECK_CBT",
            "selected_cards": ["The Tower"],
        },
    )

    assert response.status_code == 200
    payload = response.json()["output"]
    assert payload["summary"] == "dynamic prompt ok"


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


def test_analytics_endpoint_ranks_cognitive_distortions():
    client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-analytics",
            "user_story": "실수하면 모든 게 망가진 것처럼 느껴집니다.",
            "drawn_card": "The Tower",
            "plan": "PREMIUM",
            "preferred_school": "BECK_CBT",
        },
    )
    client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-analytics",
            "user_story": "실패를 반복하면 나는 역시 실패자라고 느낍니다.",
            "drawn_card": "The Magician",
            "plan": "PREMIUM",
            "preferred_school": "BECK_CBT",
        },
    )

    response = client.get("/api/v1/therapy/analytics/user-analytics")
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "user-analytics"
    assert body["total_entries"] == 2
    assert body["distribution_profile"]["all_or_nothing"] >= 0.0
    assert body["distribution_profile"]["overgeneralization"] >= 0.0
    assert body["ranked_patterns"][0]["pattern"] in {"all_or_nothing", "overgeneralization"}


def test_analytics_endpoint_returns_empty_profile_when_no_history_exists():
    response = client.get("/api/v1/therapy/analytics/empty-analytics")
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "empty-analytics"
    assert body["total_entries"] == 0
    assert body["distribution_profile"] == {}
    assert body["ranked_patterns"] == []


def test_custom_exception_handlers_respond_with_frontend_safe_payloads():
    invalid_user_response = client.get("/api/v1/therapy/dashboard/invalid-user")
    assert invalid_user_response.status_code == 404
    invalid_user_body = invalid_user_response.json()
    assert invalid_user_body["success"] is False
    assert invalid_user_body["error"]["code"] == "INVALID_USER"

    decrypt_failure_response = client.get("/api/v1/therapy/analytics/decrypt-fail")
    assert decrypt_failure_response.status_code == 500
    decrypt_failure_body = decrypt_failure_response.json()
    assert decrypt_failure_body["success"] is False
    assert decrypt_failure_body["error"]["code"] == "DECRYPTION_FAILURE"

    invalid_persona_response = client.get("/api/v1/therapy/analytics/bad-persona")
    assert invalid_persona_response.status_code == 400
    invalid_persona_body = invalid_persona_response.json()
    assert invalid_persona_body["success"] is False
    assert invalid_persona_body["error"]["code"] == "INVALID_PERSONA"


def test_streaming_endpoint_emits_clinical_progress_events():
    client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-stream",
            "user_story": "최근 관계에서 불안을 느끼고 있습니다.",
            "drawn_card": "The Lovers",
            "plan": "PREMIUM",
            "selected_cards": ["The Lovers"],
        },
    )

    with client.stream("GET", "/api/v1/therapy/stream/user-stream") as response:
        assert response.status_code == 200
        chunks = []
        for line in response.iter_lines():
            if line:
                chunks.append(line)
            if len(chunks) >= 3:
                break

    combined_payload = "\n".join(chunks)
    assert "psychological_readiness_index" in combined_payload
    assert "tree_energy_index" in combined_payload
    assert "cognitive_distortion_analysis" in combined_payload

    parsed_messages = []
    for line in chunks:
        if line.startswith("data:"):
            parsed_messages.append(json.loads(line[5:].strip()))
    assert parsed_messages
    assert any(message.get("type") == "progress" for message in parsed_messages)


def test_streaming_endpoint_stops_cleanly_when_client_disconnects():
    client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-stream-disconnect",
            "user_story": "스트레스와 불안을 관리하려고 합니다.",
            "drawn_card": "The Hermit",
            "plan": "PREMIUM",
        },
    )

    with client.stream("GET", "/api/v1/therapy/stream/user-stream-disconnect") as response:
        assert response.status_code == 200
        first_line = next(response.iter_lines())
        assert first_line


def test_dashboard_and_analytics_use_cache_until_data_changes(monkeypatch):
    monkeypatch.setenv("PURGE_AUDIT_TOKEN", "secure-audit-token")
    client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-cache",
            "user_story": "최근 업무 스트레스로 불안을 느끼고 있습니다.",
            "drawn_card": "The Hermit",
            "plan": "PREMIUM",
            "selected_cards": ["The Fool"],
        },
    )

    first_dashboard = client.get("/api/v1/therapy/dashboard/user-cache", params={"membership_tier": "PREMIUM"})
    second_dashboard = client.get("/api/v1/therapy/dashboard/user-cache", params={"membership_tier": "PREMIUM"})
    assert first_dashboard.status_code == 200
    assert second_dashboard.status_code == 200
    assert first_dashboard.json() == second_dashboard.json()
    assert DASHBOARD_CACHE.get("dashboard:user-cache:PREMIUM") is not None

    first_analytics = client.get("/api/v1/therapy/analytics/user-cache")
    second_analytics = client.get("/api/v1/therapy/analytics/user-cache")
    assert first_analytics.status_code == 200
    assert second_analytics.status_code == 200
    assert first_analytics.json() == second_analytics.json()
    assert ANALYTICS_CACHE.get("user-cache") is not None

    client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-cache",
            "user_story": "이제 더 안정감을 찾고 있습니다.",
            "drawn_card": "The Magician",
            "plan": "PREMIUM",
            "selected_cards": ["The Magician"],
        },
    )

    invalidated_dashboard = client.get("/api/v1/therapy/dashboard/user-cache", params={"membership_tier": "PREMIUM"})
    invalidated_analytics = client.get("/api/v1/therapy/analytics/user-cache")
    assert invalidated_dashboard.status_code == 200
    assert invalidated_analytics.status_code == 200
    assert invalidated_dashboard.json()["history_length"] >= 2
    assert invalidated_analytics.json()["total_entries"] >= 2


def test_purge_invalidates_cached_dashboard_and_analytics(monkeypatch):
    monkeypatch.setenv("PURGE_AUDIT_TOKEN", "secure-audit-token")
    client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-cache-purge",
            "user_story": "삭제 전 캐시를 채워 둡니다.",
            "drawn_card": "The Tower",
            "plan": "PREMIUM",
        },
    )
    client.get("/api/v1/therapy/dashboard/user-cache-purge", params={"membership_tier": "PREMIUM"})
    client.get("/api/v1/therapy/analytics/user-cache-purge")

    assert DASHBOARD_CACHE.get("dashboard:user-cache-purge:PREMIUM") is not None
    assert ANALYTICS_CACHE.get("user-cache-purge") is not None

    response = client.request(
        "DELETE",
        "/api/v1/therapy/purge",
        json={"user_id": "user-cache-purge"},
        headers={"X-Audit-Token": "secure-audit-token"},
    )

    assert response.status_code == 200
    assert DASHBOARD_CACHE.get("dashboard:user-cache-purge:PREMIUM") is None
    assert ANALYTICS_CACHE.get("user-cache-purge") is None


def test_purge_requires_audit_token_header(monkeypatch):
    monkeypatch.setenv("PURGE_AUDIT_TOKEN", "secure-audit-token")
    client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-purge-protected",
            "user_story": "보호된 데이터를 삭제하려고 합니다.",
            "drawn_card": "The Hermit",
            "plan": "PREMIUM",
        },
    )

    response = client.request(
        "DELETE",
        "/api/v1/therapy/purge",
        json={"user_id": "user-purge-protected"},
    )

    assert response.status_code == 401
    assert "user-purge-protected" in PSYCHOLOGY_DATABASE
    assert "user-purge-protected" not in PURGED_USERS


def test_purge_rejects_invalid_audit_token(monkeypatch):
    monkeypatch.setenv("PURGE_AUDIT_TOKEN", "secure-audit-token")
    client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-purge-invalid-token",
            "user_story": "잘못된 토큰으로는 삭제할 수 없어야 합니다.",
            "drawn_card": "The Magician",
            "plan": "PREMIUM",
        },
    )

    response = client.request(
        "DELETE",
        "/api/v1/therapy/purge",
        json={"user_id": "user-purge-invalid-token"},
        headers={"X-Audit-Token": "wrong-token"},
    )

    assert response.status_code == 403
    assert "user-purge-invalid-token" in PSYCHOLOGY_DATABASE
    assert "user-purge-invalid-token" not in PURGED_USERS


def test_purge_commits_with_valid_token_and_writes_security_audit_log(monkeypatch, tmp_path):
    monkeypatch.setenv("PURGE_AUDIT_TOKEN", "secure-audit-token")
    audit_log_path = tmp_path / "purge_audit.jsonl"
    monkeypatch.setenv("PURGE_AUDIT_LOG_PATH", str(audit_log_path))

    client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-purge-commit",
            "user_story": "감사 로그가 기록되어야 합니다.",
            "drawn_card": "The Lovers",
            "plan": "PREMIUM",
        },
    )

    response = client.request(
        "DELETE",
        "/api/v1/therapy/purge",
        json={"user_id": "user-purge-commit"},
        headers={"X-Audit-Token": "secure-audit-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "purged"
    assert body["user_id"] == "user-purge-commit"
    assert "user-purge-commit" not in PSYCHOLOGY_DATABASE
    assert "user-purge-commit" in PURGED_USERS

    assert audit_log_path.exists()
    audit_lines = audit_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(audit_lines) == 1
    audit_entry = json.loads(audit_lines[0])
    assert audit_entry["user_id"] == "user-purge-commit"
    assert audit_entry["action_type"] == "PURGE_COMMITTED"
    assert "T" in audit_entry["timestamp"]
    assert "user_story" not in audit_entry
    assert "output" not in audit_entry


def test_backoffice_analytics_summary_reports_empty_fallback_profile():
    response = client.get("/api/v1/backoffice/analytics/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["total_records"] == 0
    assert body["preferred_school_distribution"] == {"FREUDIAN": 0.0, "ROGERIAN": 0.0, "BECK_CBT": 0.0}
    assert body["tree_energy_variance"] == 0.0
    assert body["ranked_detected_cognitive_distortions"] == []


def test_backoffice_analytics_summary_aggregates_virtual_db_metrics():
    client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-backoffice-summary",
            "user_story": "관계 문제로 자존감이 흔들립니다.",
            "drawn_card": "The Lovers",
            "plan": "PREMIUM",
            "preferred_school": "FREUDIAN",
            "selected_cards": ["The Lovers"],
        },
    )
    client.post(
        "/api/v1/therapy/read",
        json={
            "user_id": "user-backoffice-summary-2",
            "user_story": "실패를 반복하면 나는 실패자라고 느낍니다.",
            "drawn_card": "The Tower",
            "plan": "PREMIUM",
            "preferred_school": "BECK_CBT",
            "selected_cards": ["The Tower"],
        },
    )

    response = client.get("/api/v1/backoffice/analytics/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["total_records"] >= 2
    assert body["preferred_school_distribution"]["FREUDIAN"] >= 0.0
    assert body["preferred_school_distribution"]["BECK_CBT"] >= 0.0
    assert body["tree_energy_variance"] >= 0.0
    assert body["ranked_detected_cognitive_distortions"]


def test_backoffice_samples_and_purge_work(monkeypatch):
    monkeypatch.setenv("PURGE_AUDIT_TOKEN", "secure-audit-token")
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
