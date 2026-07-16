"""Freud/Jung trailing JSON metrics parser."""
from __future__ import annotations

from app.services.freud_jung_tracker import (
    build_psychodynamic_output_directive,
    ensure_psychodynamic_metrics,
    extract_psychodynamic_metrics,
    metrics_to_json_line,
    normalize_psychodynamic_metrics,
)


def test_output_directive_contains_keys():
    text = build_psychodynamic_output_directive()
    assert "ego_id_conflict" in text
    assert "shadow_index" in text
    assert "persona_fatigue" in text
    assert "dominant_archetype" in text
    assert "defense_mechanism" in text
    assert "OUTPUT FORMAT RULE" in text


def test_extract_trailing_json_line():
    prose = "카드가 마음을 살짝 비춰 주네요. 어떤 장면이 남나요?"
    metrics = {
        "ego_id_conflict": 72,
        "shadow_index": 55,
        "persona_fatigue": 61,
        "dominant_archetype": "그림자",
        "defense_mechanism": "투사",
    }
    raw = prose + "\n" + metrics_to_json_line(metrics)
    display, parsed = extract_psychodynamic_metrics(raw)
    assert display == prose
    assert parsed["ego_id_conflict"] == 72
    assert parsed["dominant_archetype"] == "그림자"
    assert "```" not in display


def test_ensure_fallback_when_missing():
    display, metrics = ensure_psychodynamic_metrics(
        "사람들이 앞에서 괜찮은 척하느라 지쳤어요.",
        user_text="괜찮은 척하느라 너무 지치고 숨기고 싶어요",
    )
    assert "ego_id_conflict" in metrics
    assert 0 <= metrics["shadow_index"] <= 100
    assert metrics["dominant_archetype"]
    assert display  # still has prose
    assert "{" not in display or "ego_id_conflict" not in display


def test_normalize_clamps():
    m = normalize_psychodynamic_metrics(
        {"ego_id_conflict": 140, "shadow_index": -3, "persona_fatigue": "88", "dominant_archetype": "페르소나"}
    )
    assert m["ego_id_conflict"] == 100
    assert m["shadow_index"] == 0
    assert m["persona_fatigue"] == 88
