from __future__ import annotations

from typing import Any, Dict, List

from app.assessments.base import AssessmentInstrument, AssessmentItem, ResponseType

AGREE_OPTIONS = [
    {"value": 0, "label": "전혀 아님"},
    {"value": 1, "label": "아닌 편"},
    {"value": 2, "label": "보통"},
    {"value": 3, "label": "그런 편"},
    {"value": 4, "label": "매우 그럼"},
]


class RSESInstrument(AssessmentInstrument):
    instrument_id = "rses"
    display_name = "RSES (자존감)"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem("rses", "rses_q1", "전반적으로 나는 실패자라고 느끼는 편이다.", ResponseType.SINGLE_CHOICE, AGREE_OPTIONS, "자기 평가에 대한 질문이에요. 솔직해도 괜찮아요."),
            AssessmentItem("rses", "rses_q2", "나는 내가 좋은 점이 있다고 느낀다.", ResponseType.SINGLE_CHOICE, AGREE_OPTIONS, "반대 방향의 질문도 하나 더 여쭤볼게요."),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        q1 = answers.get("rses_q1", 2)
        q2 = answers.get("rses_q2", 2)
        score = (4 - max(0, min(4, int(q1)))) + max(0, min(4, int(q2)))
        completed = len([k for k in answers if k.startswith("rses_")])
        return {"instrument": self.instrument_id, "completed_items": completed, "total_items": 2, "partial_score": score, "completion_rate": round(completed / 2, 2), "severity_hint": "low" if score <= 3 else "healthy" if score >= 6 else "moderate"}


class AttachmentECRInstrument(AssessmentInstrument):
    instrument_id = "attachment_ecr"
    display_name = "애착 불안·회피 (단축)"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem("attachment_ecr", "ecr_anxiety", "관계에서 버림받을까 봐 자주 걱정되나요?", ResponseType.SINGLE_CHOICE, AGREE_OPTIONS, "관계 패턴을 이해하는 데 도움이 돼요."),
            AssessmentItem("attachment_ecr", "ecr_avoidance", "가까워지면 불편해서 거리를 두고 싶어지나요?", ResponseType.SINGLE_CHOICE, AGREE_OPTIONS, "친밀감과 거리감 모두 살펴볼게요."),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        anxiety = max(0, min(4, int(answers.get("ecr_anxiety", 2))))
        avoidance = max(0, min(4, int(answers.get("ecr_avoidance", 2))))
        completed = len([k for k in answers if k.startswith("ecr_")])
        return {
            "instrument": self.instrument_id,
            "completed_items": completed,
            "total_items": 2,
            "attachment_anxiety": round(anxiety / 4, 2),
            "attachment_avoidance": round(avoidance / 4, 2),
            "completion_rate": round(completed / 2, 2),
            "severity_hint": "insecure" if anxiety >= 3 or avoidance >= 3 else "secure",
        }
