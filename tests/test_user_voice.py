"""Tests for user-friendly assessment voice layer."""
from __future__ import annotations

from app.assessments.base import AssessmentItem, ResponseType
from app.assessments.sct import SCTInstrument
from app.assessments.user_voice import enrich_assessment_payload, user_instrument_title
from app.services.orchestrator import _serialize_assessment


def test_user_instrument_title_hides_jargon():
    assert "PHQ" not in user_instrument_title("phq9")
    assert user_instrument_title("sct") == "문장 이어쓰기 · 마음 글씨"


def test_enrich_assessment_payload_rewrites_rses():
    payload = enrich_assessment_payload(
        {
            "instrument": "rses",
            "item_id": "rses_q1",
            "prompt": "전반적으로 나는 실패자라고 느끼는 편이다.",
            "response_type": "single_choice",
            "options": [{"value": 0, "label": "전혀 아님"}],
            "framing": "자기 평가에 대한 질문이에요.",
        }
    )
    assert "실패자" not in payload["prompt"]
    assert "자신" in payload["prompt"]
    assert payload["user_title"] == "나 자신을 바라보는 마음"
    assert payload["options"][0]["label"] == "전혀 그렇지 않아요"


def test_serialize_assessment_applies_user_voice():
    item = AssessmentItem(
        instrument="sct",
        item_id="sct_self",
        prompt="나에게 '나'란 …",
        response_type=ResponseType.OPEN_TEXT,
        options=[],
        conversational_framing="이어 써 주세요.",
    )
    out = _serialize_assessment(item)
    assert out["response_type"] == "open_text"
    assert out["user_title"] == "문장 이어쓰기 · 마음 글씨"
    assert "자신" in out["prompt"] or "자신" in out.get("framing", "")
    assert out.get("efficacy", {}).get("seeds")
    assert out["efficacy"]["affirmation"]


def test_sct_scores_text_answers():
    inst = SCTInstrument()
    score = inst.score_partial(
        {
            "sct_self": "나는 요즘 불안하고 힘들어요",
            "sct_stress": "힘들 때 혼자 있고 싶어요",
        }
    )
    assert score["completed_items"] == 2
    assert score.get("spectrum_signals")
