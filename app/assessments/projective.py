from __future__ import annotations

from typing import Any, Dict, List

from app.assessments.base import AssessmentInstrument, AssessmentItem, ResponseType

HTP_OPTIONS = {
    "house": [
        {"value": 0, "label": "안정적·단정함"},
        {"value": 1, "label": "폐쇄적·작음"},
        {"value": 2, "label": "불안정·손상됨"},
        {"value": 3, "label": "화려·크게 표현"},
    ],
    "tree": [
        {"value": 0, "label": "튼튼·생명력 있음"},
        {"value": 1, "label": "마른·시들음"},
        {"value": 2, "label": "뿌리 약함·흔들림"},
        {"value": 3, "label": "가시·뾰족함"},
    ],
    "person": [
        {"value": 0, "label": "열린·정면"},
        {"value": 1, "label": "작거나 뒤돌음"},
        {"value": 2, "label": "긴장·각진"},
        {"value": 3, "label": "크고 중심적"},
    ],
}

TAROT_OPTIONS = [
    {"value": 0, "label": "The Fool — 새로운 시작"},
    {"value": 1, "label": "The Hermit — 고독·성찰"},
    {"value": 2, "label": "The Tower — 붕괴·변화"},
    {"value": 3, "label": "The Lovers — 관계·선택"},
    {"value": 4, "label": "The Magician — 통제·의지"},
]


class HTPProjectiveInstrument(AssessmentInstrument):
    instrument_id = "htp"
    display_name = "HTP 투사 (집·나무·사람)"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem("htp", "htp_house", "지금 마음이 '집'에 비유된다면 어떤 느낌인가요?", ResponseType.SINGLE_CHOICE, HTP_OPTIONS["house"], "그림 대신 상상으로 가볍게 해볼게요."),
            AssessmentItem("htp", "htp_tree", "당신의 '나무(생명력)'는 지금 어떤 상태에 가깝나요?", ResponseType.SINGLE_CHOICE, HTP_OPTIONS["tree"], "성장과 에너지를 살펴볼게요."),
            AssessmentItem("htp", "htp_person", "마음속 '사람(자기/타인)'의 모습은 어떤가요?", ResponseType.SINGLE_CHOICE, HTP_OPTIONS["person"], "관계적 자기상에 대한 질문이에요."),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        valid = {k: v for k, v in answers.items() if k.startswith("htp_")}
        return {
            "instrument": self.instrument_id,
            "completed_items": len(valid),
            "total_items": 3,
            "house_code": valid.get("htp_house"),
            "tree_energy_sign": valid.get("htp_tree"),
            "person_relational_tag": valid.get("htp_person"),
            "completion_rate": round(len(valid) / 3, 2),
            "severity_hint": "projective_complete" if len(valid) >= 2 else "partial",
        }


class TarotProjectiveInstrument(AssessmentInstrument):
    instrument_id = "tarot_reflect"
    display_name = "타로 상징 투사"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem(
                "tarot_reflect",
                "tarot_card",
                "지금 마음에 가장 가까운 카드 상징을 골라 주세요.",
                ResponseType.SINGLE_CHOICE,
                TAROT_OPTIONS,
                "타로는 진단이 아니라 자기 성찰 도구예요.",
            ),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        card = answers.get("tarot_card")
        archetype_map = {0: "innocent", 1: "sage", 2: "destroyer", 3: "lover", 4: "magician"}
        return {
            "instrument": self.instrument_id,
            "completed_items": 1 if card is not None else 0,
            "total_items": 1,
            "archetype": archetype_map.get(int(card), "unknown"),
            "completion_rate": 1.0 if card is not None else 0.0,
            "severity_hint": "symbolic",
        }
