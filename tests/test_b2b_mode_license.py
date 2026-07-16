"""Patent/B2B: mode analyzers, license types, PII mask, SOS."""
from __future__ import annotations

from app.db.database import init_db, reset_db
from app.models.commercial_license import LicenseType, is_b2b_license, license_type_from_discipline
from app.services.b2b_privacy import anonymize_pii, maybe_anonymize_for_license
from app.services.b2b_sos import evaluate_sos_triggers, list_org_sos_alerts, maybe_trigger_b2b_sos
from app.services.chat_session import ChatSessionState
from app.services.commercial_license_context import resolve_license_context, save_license_context
from app.services.emotional_pattern import (
    analyze_personal_pattern,
    build_user_emotional_pattern,
    record_pattern_from_chat_session,
    save_emotional_pattern,
)
from app.services.mode_analyzers import detect_cbt_15_distortions, run_mode_specific_analyzer


def test_license_type_mapping_and_b2b_flag():
    assert license_type_from_discipline("counseling_society") == LicenseType.B2B_SOCIETY_GENERAL.value
    assert license_type_from_discipline("psychiatry_society") == LicenseType.B2B_SOCIETY_MEDICAL.value
    assert license_type_from_discipline("faith_counseling_society") == LicenseType.B2B_SOCIETY_FAITH.value
    assert is_b2b_license("B2B_society_faith") is True
    assert is_b2b_license("B2C_personal") is False


def test_cbt15_and_faith_analyzers_branch():
    psych = run_mode_specific_analyzer(
        "psychology",
        "항상 완전 망했고 내 탓이야. 당연히 해야 해.",
    )
    assert psych["analyzerId"].startswith("psychology_cbt15")
    assert len(psych["cbt15Flags"]) >= 2
    assert "all_or_nothing" in detect_cbt_15_distortions("완전 전부 항상 망했어")

    faith = run_mode_specific_analyzer(
        "faith",
        "하나님이 벌하시는 것 같고 영적 탈진이 와요. 기도가 안 돼요.",
    )
    assert faith["consultationMode"] == "faith"
    assert faith["spiritualDryness"]["detected"] is True
    assert faith["spiritualDistortionFlags"]


def test_pii_mask_and_sos_for_b2b_only():
    reset_db()
    init_db(force=True)

    masked, hits = anonymize_pii("저는 김민수예요. 010-1234-5678로 전화주세요. test@example.com")
    assert "[비식별화]" in masked
    assert hits.get("phone") or hits.get("email") or hits.get("name")

    b2c = maybe_anonymize_for_license("저는 김민수예요", license_type="B2C_personal")
    assert b2c["masked"] is False

    save_license_context("sos-user", license_type="B2B_society_general", organization_id="org-sos-1")
    for i in range(5):
        save_emotional_pattern(
            build_user_emotional_pattern(
                user_id="sos-user",
                session_id=f"base-{i}",
                sud_scores={"preSessionSUD": 4, "postSessionSUD": 3.5},
                cognitive_metrics={"cognitiveDistortionFlags": ["rumination"], "coreWordFrequencies": ["불안"]},
            )
        )
    save_emotional_pattern(
        build_user_emotional_pattern(
            user_id="sos-user",
            session_id="crisis",
            sud_scores={"preSessionSUD": 9.2, "postSessionSUD": 9.0},
            cognitive_metrics={
                "cognitiveDistortionFlags": ["all_or_nothing", "magnification", "personalization", "blaming"],
                "coreWordFrequencies": ["우울"],
            },
        )
    )
    analysis = analyze_personal_pattern("sos-user")
    evaluation = evaluate_sos_triggers(pattern_analysis=analysis, latest_sud=9.0)
    assert evaluation["should_alert"] is True

    # B2C must not enqueue
    assert (
        maybe_trigger_b2b_sos(
            license_type="B2C_personal",
            org_id="org-sos-1",
            user_id="sos-user",
            consultation_mode="psychology",
            pattern_analysis=analysis,
            latest_sud=9.0,
            messages=[{"role": "user", "content": "저는 김민수예요 010-9999-8888"}],
        )
        is None
    )

    alert = maybe_trigger_b2b_sos(
        license_type="B2B_society_general",
        org_id="org-sos-1",
        user_id="sos-user",
        consultation_mode="psychology",
        session_id="crisis",
        pattern_analysis=analysis,
        latest_sud=9.0,
        messages=[{"role": "user", "content": "저는 김민수예요 010-9999-8888"}],
    )
    assert alert is not None
    payload_text = str(alert["payload"])
    assert "010-9999-8888" not in payload_text
    alerts = list_org_sos_alerts("org-sos-1", status="pending")
    assert alerts


def test_session_license_fields_flow_into_pattern_extra():
    reset_db()
    init_db(force=True)
    uid = "lic-session-user"
    save_license_context(uid, license_type="B2B_society_faith", organization_id="org-faith-1")
    state = ChatSessionState(session_id="faith-1", user_id=uid)
    state.consultation_mode = "faith"
    state.license_type = "B2B_society_faith"
    state.organization_id = "org-faith-1"
    state.org_id = "org-faith-1"
    state.messages = [
        {"role": "user", "content": "하나님이 저를 버리신 것 같고 영적 메마름이 심해요."},
    ]
    state.persona_routing = {"school": "ROGERIAN", "mood_state": "VULNERABLE", "detected_distortions": []}
    state.quant_features = {"psychiatric_stress_weight": 0.8}

    doc = record_pattern_from_chat_session(uid, state, pre_sud=8.5, post_sud=8.0)
    assert doc["extra"]["licenseType"] == "B2B_society_faith"
    assert doc["extra"]["consultationMode"] == "faith"
    assert doc["cognitiveMetrics"].get("modeAnalyzer", {}).get("consultationMode") == "faith"

    ctx = resolve_license_context(uid, session=state)
    assert ctx["b2b"] is True
    assert ctx["organizationId"] == "org-faith-1"
