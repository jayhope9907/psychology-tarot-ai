from app.services.emotional_spectrum import (
    UnifiedEmotionalSpectrumEngine,
    build_spectrum_prompt_block,
    compute_emotional_spectrum,
    parse_clinical_state_to_room,
    resolve_base_scores_from_sanitized,
)

ENGINE = UnifiedEmotionalSpectrumEngine()


def test_normal_low_signal():
    result = ENGINE.calculate_internalizing_spectrum(
        {"depressive": 10, "anxiety": 10, "somatic": 5},
        {},
    )
    assert result["internalizing_risk_level"] == "NORMAL"
    assert result["suggested_approach"] == "PROST_CONFRONTATION"
    assert 0 <= result["total_internalizing_score"] <= 100
    assert result["non_diagnostic"] is True


def test_comorbidity_synergy_amplifies():
    solo = ENGINE.calculate_internalizing_spectrum(
        {"depressive": 90, "anxiety": 0, "somatic": 0}, {}
    )
    combined = ENGINE.calculate_internalizing_spectrum(
        {"depressive": 90, "anxiety": 90, "somatic": 0}, {}
    )
    # 우울 단독보다 우울+불안 결합이 시너지 항으로 훨씬 커야 함
    assert combined["total_internalizing_score"] > solo["total_internalizing_score"] + 20


def test_high_alert_and_clamp():
    result = ENGINE.calculate_internalizing_spectrum(
        {"depressive": 100, "anxiety": 100, "somatic": 100},
        {"hesitation_index": 1.0, "backspace_count": 50, "word_delay_ms": 9999},
    )
    assert result["internalizing_risk_level"] == "HIGH_ALERT"
    assert result["suggested_approach"] == "SUNG_AH_SUPPORT"
    assert result["total_internalizing_score"] <= 100.0
    dims = result["dimensions"]
    for key in ("depressive_index", "anxiety_index", "obsessive_compulsive", "panic_index"):
        assert 0 <= dims[key] <= 100


def test_schizo_signal_forces_support_agent():
    result = ENGINE.calculate_internalizing_spectrum(
        {"depressive": 10, "anxiety": 10, "somatic": 0},
        {"loose_association_score": 0.8, "ego_boundary_loss_score": 0.7},
    )
    assert result["internalizing_risk_level"] == "NORMAL"
    assert result["suggested_approach"] == "SUNG_AH_SUPPORT"
    sch = result["dimensions"]["schizophrenia_spectrum"]
    assert sch["loose_association"] == 80.0
    assert sch["delusional_affinity"] == 72.0


def test_behavioral_metrics_shape_ocd_panic():
    calm = ENGINE.calculate_internalizing_spectrum(
        {"anxiety": 50}, {"hesitation_index": 0.0, "backspace_count": 0, "word_delay_ms": 0}
    )
    tense = ENGINE.calculate_internalizing_spectrum(
        {"anxiety": 50}, {"hesitation_index": 0.9, "backspace_count": 20, "word_delay_ms": 5000}
    )
    assert tense["dimensions"]["obsessive_compulsive"] > calm["dimensions"]["obsessive_compulsive"]
    assert tense["dimensions"]["panic_index"] > calm["dimensions"]["panic_index"]


def test_room_layout_branches():
    fractured = parse_clinical_state_to_room(
        {
            "total_internalizing_score": 30,
            "dimensions": {"schizophrenia_spectrum": {"loose_association": 80, "ego_boundary_loss": 60}},
        }
    )
    assert fractured["color_tone"] == "fractured-distorted"
    assert fractured["wall_symmetry"] == "broken"
    assert fractured["agent_persona"] == "SUNG_AH_SUPPORT"

    rigid = parse_clinical_state_to_room(
        {
            "total_internalizing_score": 85,
            "suggested_approach": "SUNG_AH_SUPPORT",
            "dimensions": {"schizophrenia_spectrum": {"loose_association": 0, "ego_boundary_loss": 0}},
        }
    )
    assert rigid["color_tone"] == "dark-gray"
    assert rigid["lighting_level"] == 15
    assert rigid["wall_symmetry"] == "rigid"

    warm = parse_clinical_state_to_room(
        {"total_internalizing_score": 20, "dimensions": {}}
    )
    assert warm["color_tone"] == "warm-yellow"
    assert warm["lighting_level"] == 85


def test_base_scores_from_sanitized_proxy():
    scores = resolve_base_scores_from_sanitized(
        {"initialWeights": {"mood": 20, "energy": 30, "anxiety": 70}}
    )
    assert scores["depressive"] == 80.0
    assert scores["anxiety"] == 70.0
    assert scores["somatic"] == 70.0
    default = resolve_base_scores_from_sanitized(None)
    assert default == {"depressive": 50.0, "anxiety": 50.0, "somatic": 50.0}


def test_compute_includes_room_and_prompt_gating():
    result = compute_emotional_spectrum(
        sanitized={"initialWeights": {"mood": 10, "energy": 20, "anxiety": 90}},
        behavioral_metrics={"hesitation_index": 0.8, "backspace_count": 15, "word_delay_ms": 4000},
    )
    assert "mind_room" in result
    assert result["mind_room"]["color_tone"] in ("dark-gray", "fractured-distorted", "warm-yellow")
    block = build_spectrum_prompt_block(result)
    if result["internalizing_risk_level"] != "NORMAL":
        assert "내담자에게 수치" in block
        assert "비진단" in block
    calm = compute_emotional_spectrum(
        sanitized={"initialWeights": {"mood": 90, "energy": 90, "anxiety": 5}},
        behavioral_metrics={},
    )
    assert build_spectrum_prompt_block(calm) == ""
