"""SCT(문장완성) — 사용자 친화적 문장 이어쓰기."""
from __future__ import annotations

from typing import Any, Dict, List

from app.assessments.base import AssessmentInstrument, AssessmentItem, ResponseType
from app.services.dsm5_framework import score_text_against_spectra

SCT_ITEMS = [
    (
        "sct_self",
        "나에게 '나'란 …",
        "지금 자신에 대해 떠오르는 말을 이어 써 주세요.",
    ),
    (
        "sct_stress",
        "힘들 때 나는 …",
        "스트레스·슬픔·화가 날 때 마음이나 행동을 적어 주세요.",
    ),
    (
        "sct_future",
        "앞으로 나는 …",
        "미래에 대한 희망·걱정·바람을 이어 써 주세요.",
    ),
]


class SCTInstrument(AssessmentInstrument):
    instrument_id = "sct"
    display_name = "문장완성 · 마음 글씨 (SCT)"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem(
                instrument=self.instrument_id,
                item_id=item_id,
                prompt=stem,
                response_type=ResponseType.OPEN_TEXT,
                options=[],
                conversational_framing=framing,
                weight=1.0,
            )
            for item_id, stem, framing in SCT_ITEMS
        ]

    def score_partial(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        valid = {k: v for k, v in answers.items() if k.startswith("sct_") and str(v).strip()}
        blob = " ".join(str(v) for v in valid.values())
        spectra = score_text_against_spectra(blob) if blob else {}
        top_score = max(spectra.values()) if spectra else 0.0
        severity = "minimal"
        if top_score >= 0.55:
            severity = "moderate"
        elif top_score >= 0.3:
            severity = "mild"
        return {
            "instrument": self.instrument_id,
            "completed_items": len(valid),
            "total_items": len(self.items()),
            "spectrum_signals": spectra,
            "completion_rate": round(len(valid) / max(1, len(self.items())), 2),
            "severity_hint": severity if len(valid) >= 1 else "insufficient_data",
            "qualitative_summary": blob[:240] if blob else "",
        }
