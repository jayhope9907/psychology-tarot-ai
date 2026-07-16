"""Regression: distress keywords + psychodynamic parse order."""
from __future__ import annotations

from app.services.fatigue_manager import detect_distress
from app.services.freud_jung_tracker import ensure_psychodynamic_metrics, metrics_to_json_line


def test_distress_detects_persona_masking_fatigue():
    assert detect_distress("괜찮은 척하느라 너무 지치고 숨기고 싶어요") is True
    assert detect_distress("오늘 날씨 좋네요") is False


def test_metrics_survive_when_json_appended_to_chatbotish_prose():
    prose = (
        "괜찮은 척하느라 지친 마음이 느껴져요. "
        "사람들 앞에서 버티는 그 장면, 어떤 순간에 가장 숨고 싶어지나요?"
    )
    metrics = {
        "ego_id_conflict": 66,
        "shadow_index": 71,
        "persona_fatigue": 80,
        "dominant_archetype": "페르소나",
        "defense_mechanism": "억압",
    }
    raw = prose + "\n" + metrics_to_json_line(metrics)
    display, parsed = ensure_psychodynamic_metrics(raw, user_text="괜찮은 척")
    assert "페르소나" == parsed["dominant_archetype"]
    assert parsed["persona_fatigue"] == 80
    assert "ego_id_conflict" not in display
    assert "괜찮은 척" in display or "지친" in display
