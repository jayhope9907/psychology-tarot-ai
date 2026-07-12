"""유저 고유 에이전트 알고리즘 · 패턴 탐지 테스트."""
from __future__ import annotations

from app.db.database import reset_db
from app.services.user_agent_algorithm import (
    apply_fingerprint_bias,
    detect_user_patterns,
    empty_fingerprint,
    evolve_fingerprint,
    get_user_agent_bundle,
    simulate_learning_pass,
)
from app.models.clinical import ClinicalSchool, MoodState


def test_fingerprint_evolves_and_gets_algo_id():
    reset_db()
    uid = "user-agent-1"
    profile = evolve_fingerprint(
        uid,
        persona_routing={
            "school": "BECK_CBT",
            "mood_state": "ANALYTICAL",
            "reason": "cognitive_distortion_signal",
            "detected_distortions": ["catastrophizing", "all_or_nothing"],
        },
        quant_features={
            "psychological_readiness_index": 0.4,
            "tree_energy_index": 0.35,
            "psychiatric_stress_weight": 0.7,
            "attachment_matrix_score": 0.55,
        },
        counseling_phase="exploration",
        message_themes=["work", "anxiety"],
    )
    fp = profile["agent_fingerprint"]
    assert fp["algo_id"].startswith("ALG-")
    assert fp["sample_turns"] == 1
    assert fp["school_priors"].get("BECK_CBT", 0) > 0
    assert fp["distortion_hist"].get("catastrophizing", 0) >= 1


def test_simulate_learning_builds_patterns():
    reset_db()
    bundle = simulate_learning_pass(
        "user-agent-2",
        [
            "회사에서 너무 불안하고 지쳐요",
            "항상 제가 잘못한 것 같아요. 최악이에요",
            "가족 관계가 또 반복해서 힘들어요",
            "잠도 안 오고 무기력해요",
            "또 회사 일 때문에 불안해요",
        ],
    )
    assert bundle["algo_id"].startswith("ALG-")
    assert bundle["agent_fingerprint"]["sample_turns"] >= 5
    assert isinstance(bundle["patterns"], list)


def test_fingerprint_bias_prefers_prior_school():
    fp = empty_fingerprint("u")
    fp["confidence"] = 0.8
    fp["school_priors"] = {"ROGERIAN": 0.7, "BECK_CBT": 0.2}
    routing = {
        "school": ClinicalSchool.BECK_CBT,
        "mood_state": MoodState.ANALYTICAL,
        "reason": "keyword",
        "persona_label": "CBT",
        "detected_distortions": [],
    }
    biased = apply_fingerprint_bias(routing, fp, user_explicit=False)
    assert biased["school"] == ClinicalSchool.ROGERIAN
    assert biased["reason"] == "user_agent_fingerprint_prior"


def test_get_bundle_api_shape():
    reset_db()
    bundle = get_user_agent_bundle("user-empty")
    assert "agent_fingerprint" in bundle
    assert "disclaimer_ko" in bundle
    assert "진단" in bundle["disclaimer_ko"]
