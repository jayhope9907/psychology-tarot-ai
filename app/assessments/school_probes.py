from __future__ import annotations

from typing import Any, Dict, List

from app.assessments.base import AssessmentInstrument, AssessmentItem, LIKERT_0_3_OPTIONS, ResponseType

YES_NO_SOMETIMES = [
    {"value": 0, "label": "아니요"},
    {"value": 1, "label": "가끔"},
    {"value": 2, "label": "자주"},
    {"value": 3, "label": "거의 항상"},
]


class CBThoughtInstrument(AssessmentInstrument):
    instrument_id = "cbt_thought"
    display_name = "CBT 자동적 사고·왜곡 탐지"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem("cbt_thought", "cbt_all_or_nothing", "실수하면 모든 게 망가진 것처럼 느껴지나요?", ResponseType.LIKERT_0_3, LIKERT_0_3_OPTIONS, "생각 패턴을 가볍게 살펴볼게요."),
            AssessmentItem("cbt_thought", "cbt_catastrophize", "최악의 상황이 벌어질 것 같다는 생각이 드나요?", ResponseType.LIKERT_0_3, LIKERT_0_3_OPTIONS, "걱정의 방식에 대한 질문이에요."),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        valid = {k: v for k, v in answers.items() if k.startswith("cbt_")}
        flags = [k.replace("cbt_", "") for k, v in valid.items() if int(v) >= 2]
        return {"instrument": self.instrument_id, "completed_items": len(valid), "total_items": 2, "cognitive_distortion_flags": flags, "completion_rate": round(len(valid) / 2, 2), "severity_hint": "elevated" if flags else "low"}


class PsychodynamicInstrument(AssessmentInstrument):
    instrument_id = "psychodynamic"
    display_name = "정신동역학 방어·반복 패턴"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem("psychodynamic", "pd_repetition", "비슷한 관계·상황이 반복되는 느낌이 있나요?", ResponseType.LIKERT_0_3, YES_NO_SOMETIMES, "반복 패턴을 탐색해 볼게요."),
            AssessmentItem("psychodynamic", "pd_defense", "힘든 감정이 올라오면 무의식적으로 피하거나 부정하나요?", ResponseType.LIKERT_0_3, YES_NO_SOMETIMES, "방어 방식에 대한 질문이에요."),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        valid = {k: v for k, v in answers.items() if k.startswith("pd_")}
        total = sum(max(0, min(3, int(v))) for v in valid.values())
        return {"instrument": self.instrument_id, "completed_items": len(valid), "total_items": 2, "defense_activation_index": round(total / 6, 2) if valid else 0.0, "completion_rate": round(len(valid) / 2, 2), "severity_hint": "active" if total >= 3 else "low"}


class BehavioralActivationInstrument(AssessmentInstrument):
    instrument_id = "behavioral"
    display_name = "행동 활성화·회피"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem("behavioral", "ba_avoidance", "해야 할 일·만남을 미루거나 피한 적이 있나요?", ResponseType.LIKERT_0_3, YES_NO_SOMETIMES, "행동 패턴도 함께 볼게요."),
            AssessmentItem("behavioral", "ba_pleasure", "예전에 즐기던 일에서 쾌감이 줄었나요?", ResponseType.LIKERT_0_3, LIKERT_0_3_OPTIONS, "활력과 즐거움에 대한 질문이에요."),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        valid = {k: v for k, v in answers.items() if k.startswith("ba_")}
        avoidance = int(valid.get("ba_avoidance", 0))
        return {"instrument": self.instrument_id, "completed_items": len(valid), "total_items": 2, "avoidance_index": round(avoidance / 3, 2), "completion_rate": round(len(valid) / 2, 2), "severity_hint": "withdrawn" if avoidance >= 2 else "active"}
