"""Regression: sanitizeAndCompensate pre-AI input gate."""
from __future__ import annotations

from app.services.input_sanitizer import (
    ARCHETYPE_NONE,
    DEFAULT_CHECKIN_WEIGHT,
    apply_mode_isolation_to_psychodynamics,
    sanitize_and_compensate,
)


def test_step1_without_card_uses_none_archetype():
    out = sanitize_and_compensate(
        {
            "consultationMode": "psychology",
            "step": 1,
            "selectedCard": "The Moon",
            "checkInMetrics": None,
        }
    )
    assert out["dominantArchetype"] == ARCHETYPE_NONE
    assert out["selectedCard"] is None
    assert out["initialWeights"] == {
        "mood": DEFAULT_CHECKIN_WEIGHT,
        "energy": DEFAULT_CHECKIN_WEIGHT,
        "anxiety": DEFAULT_CHECKIN_WEIGHT,
    }
    assert out["defenseMechanismEnabled"] is True


def test_step2_keeps_selected_card():
    out = sanitize_and_compensate(
        consultation_mode="psychology",
        step=2,
        selected_card="The Hermit",
        check_in_metrics={"mood": 70, "energy": 40},
    )
    assert out["dominantArchetype"] == "The Hermit"
    assert out["initialWeights"]["mood"] == 70
    assert out["initialWeights"]["energy"] == 40
    assert out["initialWeights"]["anxiety"] == DEFAULT_CHECKIN_WEIGHT


def test_legacy_1to5_dims_map_to_0_100():
    out = sanitize_and_compensate(
        {
            "consultationMode": "psychology",
            "step": 3,
            "selectedCard": "Strength",
            "checkInMetrics": {"mood": 3, "energy": 1, "anxiety": 5},
        }
    )
    assert out["initialWeights"]["mood"] == 50
    assert out["initialWeights"]["energy"] == 0
    assert out["initialWeights"]["anxiety"] == 100


def test_faith_mode_disables_defense_mechanism_channel():
    out = sanitize_and_compensate(
        {
            "consultationMode": "faith",
            "step": 4,
            "selectedCard": "The Star",
        }
    )
    assert out["isFaithMode"] is True
    assert out["defenseMechanismEnabled"] is False
    assert out["defenseMechanism"] is None

    metrics = apply_mode_isolation_to_psychodynamics(
        {
            "ego_id_conflict": 40,
            "shadow_index": 50,
            "persona_fatigue": 60,
            "dominant_archetype": "페르소나",
            "defense_mechanism": "억압",
        },
        consultation_mode="faith",
    )
    assert metrics["defense_mechanism"] == "inactive"
    assert metrics["defenseMechanismEnabled"] is False
    assert metrics["modeIsolated"] is True
