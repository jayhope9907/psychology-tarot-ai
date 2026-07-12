"""MBTI 선호 탐색 — 유형 확정이 아닌 에너지·정보·결정·생활 스타일 자기이해."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.assessments.base import AssessmentInstrument, AssessmentItem, ResponseType

PAIR_OPTIONS = [
    {"value": 0, "label": "왼쪽(A)에 가까워요"},
    {"value": 1, "label": "조금 왼쪽"},
    {"value": 2, "label": "조금 오른쪽"},
    {"value": 3, "label": "오른쪽(B)에 가까워요"},
]

# item -> (dimension, pole_for_high_score)  high score leans toward second letter
ITEMS: List[Tuple[str, str, str, str, str]] = [
    (
        "mbti_ei_1",
        "EI",
        "I",
        "에너지를 채울 때, 사람들과 함께 있는 쪽(A)과 혼자만의 시간(B) 중 어디에 더 가까우신가요?",
        "지금 하시는 일이나 관계에서 에너지가 많이 쓰이신 것 같아요. 부담 없이 취향만 알려 주세요.",
    ),
    (
        "mbti_ei_2",
        "EI",
        "I",
        "이야기할 때 바로 말로 풀어내는 편(A)인가요, 속으로 정리한 뒤 말하는 편(B)인가요?",
        "정답은 없어요. 요즘 느낌에 가까운 쪽이면 충분해요.",
    ),
    (
        "mbti_sn_1",
        "SN",
        "N",
        "정보를 볼 때 구체적인 사실·디테일(A)과 큰 그림·가능성(B) 중 어디에 끌리시나요?",
        "생각의 ‘결’을 살짝 알아보려고요.",
    ),
    (
        "mbti_sn_2",
        "SN",
        "N",
        "설명은 현실적인 예시(A)가 편한가요, 비유·의미(B)가 더 와닿나요?",
        "편한 쪽만 골라 주셔도 돼요.",
    ),
    (
        "mbti_tf_1",
        "TF",
        "F",
        "결정할 때 논리·원칙(A)과 사람·감정 영향(B) 중 어디에 더 기울어지나요?",
        "제가 보기에 감정과 관계 사이에서 고민이 있으신 듯해요. 결정 스타일만 살짝요.",
    ),
    (
        "mbti_tf_2",
        "TF",
        "F",
        "피드백을 줄 때 솔직·직접(A)과 배려·온화(B) 중 어떤 편이 더 나다운가요?",
        "어느 쪽이 ‘나답다’에 가까운지만 알려 주세요.",
    ),
    (
        "mbti_jp_1",
        "JP",
        "P",
        "일정은 미리 정해 두는 편(A)인가요, 상황에 맞춰 열어 두는 편(B)인가요?",
        "생활 리듬 취향이에요. 요즘 기준이면 충분합니다.",
    ),
    (
        "mbti_jp_2",
        "JP",
        "P",
        "마감 앞에서는 계획대로 밀어붙이는 편(A)인가요, 유연하게 바꾸는 편(B)인가요?",
        "마지막이에요. 부담 갖지 마시고 골라 주세요.",
    ),
]

LETTER_MAP = {
    "EI": ("E", "I"),
    "SN": ("S", "N"),
    "TF": ("T", "F"),
    "JP": ("J", "P"),
}


class MBTIPreferenceInstrument(AssessmentInstrument):
    instrument_id = "mbti_preference"
    display_name = "MBTI 선호 탐색 (교육용)"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem(
                instrument=self.instrument_id,
                item_id=item_id,
                prompt=prompt,
                response_type=ResponseType.LIKERT_0_3,
                options=PAIR_OPTIONS,
                conversational_framing=framing,
            )
            for item_id, _dim, _pole, prompt, framing in ITEMS
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        dim_scores: Dict[str, List[int]] = {k: [] for k in LETTER_MAP}
        meta = {item_id: (dim, pole) for item_id, dim, pole, *_ in ITEMS}
        for item_id, raw in answers.items():
            if item_id not in meta:
                continue
            dim, _ = meta[item_id]
            dim_scores[dim].append(max(0, min(3, int(raw))))

        leanings: Dict[str, Any] = {}
        type_chars: List[str] = []
        for dim, (left, right) in LETTER_MAP.items():
            vals = dim_scores.get(dim) or []
            if not vals:
                leanings[dim] = {"status": "insufficient", "left": left, "right": right}
                type_chars.append("?")
                continue
            avg = sum(vals) / len(vals)
            # 0..1.5 → left, 1.5..3 → right
            if avg < 1.35:
                letter, strength = left, round((1.35 - avg) / 1.35, 2)
            elif avg > 1.65:
                letter, strength = right, round((avg - 1.65) / 1.35, 2)
            else:
                letter, strength = f"{left}/{right}", 0.15
            leanings[dim] = {
                "letter": letter,
                "avg": round(avg, 2),
                "strength": min(1.0, max(0.0, strength)),
                "left": left,
                "right": right,
            }
            type_chars.append(letter if "/" not in letter else "?")

        code = "".join(type_chars)
        completed = sum(1 for v in dim_scores.values() if v)
        return {
            "instrument": self.instrument_id,
            "completed_items": len(answers),
            "total_items": len(ITEMS),
            "dimensions_answered": completed,
            "completion_rate": round(len(answers) / len(ITEMS), 2),
            "preference_leanings": leanings,
            "type_code_hint": code,
            "severity_hint": "preference_profile" if completed >= 3 else "insufficient_data",
            "non_diagnostic": True,
            "disclaimer_ko": (
                "MBTI는 성격 ‘진단’이 아니라 선호 경향 탐색입니다. "
                "유형 코드는 참고용 힌트이며 사람을 고정하지 않습니다."
            ),
        }
