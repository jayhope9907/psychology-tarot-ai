from app.models.clinical import ClinicalSchool
from app.services.persona_router import route_clinical_persona
from app.services.prompt_binding import PromptContextWeightBindingFactory
from app.services.vault import seal_payload, unseal_payload, write_audit_event


def test_persona_router_selects_beck_for_cognitive_distortion():
    routing = route_clinical_persona("나는 항상 실패하고 모든 게 망가져요.")
    assert routing["school"] == ClinicalSchool.BECK_CBT
    assert "all_or_nothing" in routing["detected_distortions"]


def test_persona_router_selects_rogerian_for_vulnerable_affect():
    routing = route_clinical_persona("너무 힘들고 외로워서 울고 싶어요.")
    assert routing["school"] == ClinicalSchool.ROGERIAN


def test_persona_router_respects_user_preference():
    routing = route_clinical_persona(
        "나는 항상 실패해요.",
        preferred_school=ClinicalSchool.FREUDIAN,
    )
    assert routing["school"] == ClinicalSchool.FREUDIAN
    assert routing["reason"] == "user_selected"


def test_prompt_binding_injects_quant_context_block():
    binding = PromptContextWeightBindingFactory(
        school=ClinicalSchool.BECK_CBT,
        psychological_readiness_index=0.35,
        cognitive_distortions=["all_or_nothing"],
        attachment_matrix_score=0.3,
        tree_energy_index=7.5,
        psychiatric_stress_weight=0.8,
        structural_sign="tension",
    ).build()

    assert binding["severity_multiplier"] >= 0.5
    assert "attachment_matrix_score" in binding["context_block"]
    assert binding["weights"]["homework_structure"] >= 0.5
    assert binding["weights"]["theory"] == "BECK_CBT"


def test_vault_dual_seal_requires_matching_user():
    payload = {"secret": "therapy-data", "history": []}
    token = seal_payload("user-vault", payload)
    restored = unseal_payload("user-vault", token)
    assert restored["secret"] == "therapy-data"

    try:
        unseal_payload("other-user", token)
        raised = False
    except Exception:
        raised = True
    assert raised


def test_vault_audit_event_writes_encrypted_line(tmp_path, monkeypatch):
    audit_path = tmp_path / "security_audit.jsonl"
    monkeypatch.setenv("SECURITY_AUDIT_LOG_PATH", str(audit_path))
    write_audit_event("DASHBOARD_READ", "user-audit", {"tier": "PREMIUM"})
    assert audit_path.exists()
    assert len(audit_path.read_text(encoding="utf-8").strip().splitlines()) == 1
