from __future__ import annotations

from typing import Any, Dict, List

from app.assessments.base import AssessmentInstrument, AssessmentItem, LIKERT_0_3_OPTIONS, ResponseType

LIKERT_0_4_STRESS = [
    {"value": 0, "label": "전혀 없음"},
    {"value": 1, "label": "거의 없음"},
    {"value": 2, "label": "때때로"},
    {"value": 3, "label": "자주"},
    {"value": 4, "label": "매우 자주"},
]


class ISIInstrument(AssessmentInstrument):
    instrument_id = "isi"
    display_name = "ISI (불면 척도)"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem("isi", "isi_q1", "잠들기 어려웠던 적이 있었나요?", ResponseType.LIKERT_0_3, LIKERT_0_3_OPTIONS, "수면 이야기가 나와서 가볍게 여쭤볼게요."),
            AssessmentItem("isi", "isi_q2", "밤중에 자주 깨거나 너무 일찍 깨었나요?", ResponseType.LIKERT_0_3, LIKERT_0_3_OPTIONS, "최근 며칠을 떠올려 보시면 좋아요."),
            AssessmentItem("isi", "isi_q3", "수면 문제 때문에 낮에 불편함을 느꼈나요?", ResponseType.LIKERT_0_3, LIKERT_0_3_OPTIONS, "마지막으로 수면의 영향도 여쭤볼게요."),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        valid = {k: v for k, v in answers.items() if k.startswith("isi_")}
        total = sum(max(0, min(3, int(v))) for v in valid.values())
        return {"instrument": self.instrument_id, "completed_items": len(valid), "total_items": 3, "partial_score": total, "completion_rate": round(len(valid) / 3, 2), "severity_hint": "moderate" if total >= 5 else "mild" if total >= 2 else "minimal"}


class PSSInstrument(AssessmentInstrument):
    instrument_id = "pss"
    display_name = "PSS (지각 스트레스)"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem("pss", "pss_q1", "최근 예상치 못한 일 때문에 짜증·스트레스를 느꼈나요?", ResponseType.LIKERT_0_3, LIKERT_0_4_STRESS[:4], "스트레스 강도를 가볍게 확인해 볼게요."),
            AssessmentItem("pss", "pss_q2", "중요한 일을 통제할 수 없다고 느낀 적이 있었나요?", ResponseType.LIKERT_0_3, LIKERT_0_4_STRESS[:4], "통제감과 관련된 질문이에요."),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        valid = {k: v for k, v in answers.items() if k.startswith("pss_")}
        total = sum(max(0, min(3, int(v))) for v in valid.values())
        return {"instrument": self.instrument_id, "completed_items": len(valid), "total_items": 2, "partial_score": total, "completion_rate": round(len(valid) / 2, 2), "severity_hint": "elevated" if total >= 4 else "normal"}


class PCL5Instrument(AssessmentInstrument):
    instrument_id = "pcl5"
    display_name = "PCL-5 (외상 스트레스 스크리닝)"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem("pcl5", "pcl5_q1", "불쾌한 기억·악몽·플래시백이 있었나요?", ResponseType.LIKERT_0_3, LIKERT_0_3_OPTIONS, "민감할 수 있는 질문이에요. 편한 만큼만 답해 주세요."),
            AssessmentItem("pcl5", "pcl5_q2", "그 일을 떠올리게 하는 것을 피하려 했나요?", ResponseType.LIKERT_0_3, LIKERT_0_3_OPTIONS, "회피 패턴도 함께 살펴볼게요."),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        valid = {k: v for k, v in answers.items() if k.startswith("pcl5_")}
        total = sum(max(0, min(3, int(v))) for v in valid.values())
        return {"instrument": self.instrument_id, "completed_items": len(valid), "total_items": 2, "partial_score": total, "completion_rate": round(len(valid) / 2, 2), "severity_hint": "screen_positive" if total >= 3 else "low"}
