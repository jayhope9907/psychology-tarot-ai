from __future__ import annotations

from typing import Any, Dict, List

from app.assessments.base import AssessmentInstrument, AssessmentItem, LIKERT_0_3_OPTIONS, ResponseType

PHQ9_ITEM_DEFINITIONS = [
    (
        "phq9_q1",
        "요즘 하루하루에 흥미나 즐거움이 줄어든 느낌이 있으셨나요?",
        "말씀 나누다 보니 한 가지만 여쁘게 여쭤볼게요.",
    ),
    (
        "phq9_q2",
        "기분이 가라앉거나, 우울하거나, 희망이 없다고 느끼신 적이 있으셨나요?",
        "조금 더 마음을 이해하고 싶어서요. 편한 만큼만 답해 주셔도 괜찮아요.",
    ),
    (
        "phq9_q3",
        "잠들기 어렵거나, 자주 깨거나, 평소보다 많이 주무신 적이 있으셨나요?",
        "수면 이야기가 나와서요. 최근 며칠 정도를 떠올려 보시면 좋겠어요.",
    ),
    (
        "phq9_q4",
        "피곤하고 기운이 없다고 느끼신 적이 있으셨나요?",
        "몸의 신호도 함께 살보면 도움이 될 것 같아요.",
    ),
    (
        "phq9_q5",
        "식욕이 줄었거나, 평소보다 많이 드신 적이 있으셨나요?",
        "마지막으로 식사 쪽도 가볍게 여쭤볼게요.",
    ),
]


class PHQ9Instrument(AssessmentInstrument):
    instrument_id = "phq9"
    display_name = "PHQ-9 (점진 도입)"

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
            for item_id, prompt, framing in PHQ9_ITEM_DEFINITIONS
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        valid = {key: value for key, value in answers.items() if key.startswith("phq9_")}
        total_score = sum(max(0, min(3, int(value))) for value in valid.values())
        completed = len(valid)
        total_items = len(self.items())
        severity = "minimal"
        if completed >= 2:
            if total_score >= 10:
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
