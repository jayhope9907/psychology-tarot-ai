from __future__ import annotations

from typing import Any, Dict, List

from app.assessments.base import AssessmentInstrument, AssessmentItem, LIKERT_0_3_OPTIONS, ResponseType

GAD7_ITEM_DEFINITIONS = [
    (
        "gad7_q1",
        "최근 며칠 동안 초조하거나, 걱정되는 마음이 자주 드셨나요?",
        "불안한 마음이 얼마나 자주 찾아오는지 가볍게 살펴볼게요.",
    ),
    (
        "gad7_q2",
        "걱정을 멈추거나 줄이기가 어려웠던 적이 있으셨나요?",
        "걱정이 머릿속을 맴도는 느낌이 있으셨는지 궁금해요.",
    ),
    (
        "gad7_q3",
        "여러 가지 일에 대해 지나치게 걱정하셨나요?",
        "대화해 보니 마음이 여러 곳으로 분산된 느낌이 있어서요.",
    ),
    (
        "gad7_q4",
        "긴장되거나 가만히 있기 어려웠던 적이 있으셨나요?",
        "몸의 긴장감도 함께 살보면 도움이 될 것 같아요.",
    ),
    (
        "gad7_q5",
        "너무 불안해서 가만히 앉아 있기 어렵거나, 계속 움직이고 싶었나요?",
        "안절부절함 쪽만요.",
    ),
    (
        "gad7_q6",
        "쉽게 짜증이 나거나, 예민해진다고 느끼셨나요?",
        "짜증·예민함 쪽이에요.",
    ),
    (
        "gad7_q7",
        "무언가 끔찍한 일이 일어날 것 같은 두려움을 자주 느끼셨나요?",
        "마지막 문항이에요. 편한 만큼만 답해 주세요.",
    ),
]


class GAD7Instrument(AssessmentInstrument):
    instrument_id = "gad7"
    display_name = "GAD-7"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem(
                instrument=self.instrument_id,
                item_id=item_id,
                prompt=prompt,
                response_type=ResponseType.LIKERT_0_3,
                options=LIKERT_0_3_OPTIONS,
                conversational_framing=framing,
                weight=1.0,
            )
            for item_id, prompt, framing in GAD7_ITEM_DEFINITIONS
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        valid = {key: value for key, value in answers.items() if key.startswith("gad7_")}
        total_score = sum(max(0, min(3, int(value))) for value in valid.values())
        completed = len(valid)
        total_items = len(self.items())
        severity = "minimal"
        if completed >= 3:
            if total_score >= 15:
                severity = "severe"
            elif total_score >= 10:
                severity = "moderate"
            elif total_score >= 5:
                severity = "mild"
        return {
            "instrument": self.instrument_id,
            "completed_items": completed,
            "total_items": total_items,
            "partial_score": total_score,
            "completion_rate": round(completed / total_items, 2) if total_items else 0.0,
            "severity_hint": severity if completed >= 2 else "insufficient_data",
        }
