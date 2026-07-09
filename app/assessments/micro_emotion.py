from __future__ import annotations

from typing import Any, Dict, List

from app.assessments.base import AssessmentInstrument, AssessmentItem, ResponseType


class EmotionScaleInstrument(AssessmentInstrument):
    instrument_id = "micro_emotion"
    display_name = "감정 온도 체크"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem(
                instrument=self.instrument_id,
                item_id="emotion_scale_0_10",
                prompt="지금 이 순간, 마음의 무게는 어느 정도로 느껴지시나요?",
                response_type=ResponseType.SCALE_0_10,
                options=[
                    {"value": 0, "label": "전혀 없어요"},
                    {"value": 2, "label": "조금"},
                    {"value": 5, "label": "보통"},
                    {"value": 7, "label": "꽤 무거워요"},
                    {"value": 10, "label": "매우 힘들어요"},
                ],
                conversational_framing="숫자로 딱 맞출 필요는 없어요. 가장 가까운 느낌을 골라 주세요.",
                weight=0.5,
            )
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        value = answers.get("emotion_scale_0_10")
        return {
            "instrument": self.instrument_id,
            "completed_items": 1 if value is not None else 0,
            "total_items": 1,
            "partial_score": int(value) if value is not None else 0,
            "completion_rate": 1.0 if value is not None else 0.0,
            "severity_hint": "check_in",
        }
