"""이상심리학 교육용 짧은 탐색 문항 — 진단이 아닌 자기성찰·대화 가이드."""
from __future__ import annotations

from typing import Any, Dict, List

from app.assessments.base import AssessmentInstrument, AssessmentItem, LIKERT_0_3_OPTIONS, ResponseType

FREQ = LIKERT_0_3_OPTIONS
SOFT = [
    {"value": 0, "label": "거의 없어요"},
    {"value": 1, "label": "가끔요"},
    {"value": 2, "label": "자주요"},
    {"value": 3, "label": "꽤 자주요"},
]

DISCLAIMER = "교육·자기성찰용 짧은 탐색이며 정신과 진단을 대체하지 않습니다."


def _score(instrument_id: str, prefix: str, answers: Dict[str, int], total_items: int) -> Dict[str, Any]:
    valid = {k: v for k, v in answers.items() if k.startswith(prefix)}
    total = sum(max(0, min(3, int(v))) for v in valid.values())
    max_score = max(1, total_items * 3)
    ratio = round(total / max_score, 3) if valid else 0.0
    hint = "low"
    if len(valid) >= max(1, total_items // 2):
        if ratio >= 0.55:
            hint = "elevated"
        elif ratio >= 0.35:
            hint = "mild"
    return {
        "instrument": instrument_id,
        "completed_items": len(valid),
        "total_items": total_items,
        "partial_score": total,
        "signal_ratio": ratio,
        "completion_rate": round(len(valid) / total_items, 2) if total_items else 0.0,
        "severity_hint": hint if valid else "insufficient_data",
        "non_diagnostic": True,
        "disclaimer_ko": DISCLAIMER,
    }


class OCDProbeInstrument(AssessmentInstrument):
    instrument_id = "ocd_probe"
    display_name = "강박 탐색 (Y-BOCS 정보제공형)"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem(
                self.instrument_id, "ocd_thoughts",
                "원하지 않는 생각·이미지가 반복해서 들어와 마음이 불편한 적이 있으셨나요?",
                ResponseType.LIKERT_0_3, SOFT,
                "제가 보기에 마음이 한곳에 자꾸 머무는 느낌이 있으신 것 같아요. 편한 만큼만 답해 주셔도 돼요.",
            ),
            AssessmentItem(
                self.instrument_id, "ocd_rituals",
                "불안을 줄이려고 같은 행동·확인을 반복하신 적이 있으신가요?",
                ResponseType.LIKERT_0_3, SOFT,
                "부담 없이, ‘자주 / 가끔’ 정도만 골라 주셔도 충분해요.",
            ),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        return _score(self.instrument_id, "ocd_", answers, 2)


class SocialAnxietyProbeInstrument(AssessmentInstrument):
    instrument_id = "social_anxiety_probe"
    display_name = "사회불안 탐색 (LSAS 정보제공형)"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem(
                self.instrument_id, "sa_fear",
                "사람 앞에서 말하거나 지켜보일 때 유난히 긴장·부끄러움을 느끼시나요?",
                ResponseType.LIKERT_0_3, SOFT,
                "관계나 사람들 사이에서 조금 지치신 느낌이 드네요. 한 가지만 여쭤볼게요.",
            ),
            AssessmentItem(
                self.instrument_id, "sa_avoid",
                "그래서 모임·통화·발표를 피하거나 미루신 적이 있으신가요?",
                ResponseType.LIKERT_0_3, SOFT,
                "피하고 싶어진 마음도 충분히 이해돼요. 정도만 알려 주세요.",
            ),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        return _score(self.instrument_id, "sa_", answers, 2)


class PanicProbeInstrument(AssessmentInstrument):
    instrument_id = "panic_probe"
    display_name = "공황 반응 탐색 (PDSS 정보제공형)"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem(
                self.instrument_id, "panic_surge",
                "갑자기 심장 두근거림·숨 가쁨·극심한 불안이 밀려온 적이 있으셨나요?",
                ResponseType.LIKERT_0_3, SOFT,
                "몸이 먼저 놀란 경험이 있으신지, 부담 없이 여쭤볼게요.",
            ),
            AssessmentItem(
                self.instrument_id, "panic_worry",
                "그런 느낌이 또 올까 봐 걱정되거나 특정 장소를 피하게 되나요?",
                ResponseType.LIKERT_0_3, SOFT,
                "다시 올까 봐 조심스러워지는 마음도 자연스러울 수 있어요.",
            ),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        return _score(self.instrument_id, "panic_", answers, 2)


class ManiaProbeInstrument(AssessmentInstrument):
    instrument_id = "mania_probe"
    display_name = "기분 고조 탐색 (MDQ 정보제공형)"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem(
                self.instrument_id, "mania_energy",
                "평소와 다르게 에너지·말이 매우 많아지거나 잠이 거의 필요 없던 시기가 있었나요?",
                ResponseType.LIKERT_0_3, SOFT,
                "기분의 ‘고조’ 쪽도 가끔 함께 보면 도움이 돼요. 편한 만큼만요.",
            ),
            AssessmentItem(
                self.instrument_id, "mania_impulse",
                "그 시기에 평소보다 충동적인 결정이나 큰 결정을 하신 적이 있으신가요?",
                ResponseType.LIKERT_0_3, SOFT,
                "잘잘못을 따지려는 질문이 아니에요. 패턴만 살짝 볼게요.",
            ),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        return _score(self.instrument_id, "mania_", answers, 2)


class ADHDProbeInstrument(AssessmentInstrument):
    instrument_id = "adhd_probe"
    display_name = "주의·실행기능 탐색 (ASRS 정보제공형)"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem(
                self.instrument_id, "adhd_focus",
                "일·대화를 끝까지 집중하기 어렵거나 자주 놓치는 느낌이 있으신가요?",
                ResponseType.LIKERT_0_3, SOFT,
                "하고 계신 일이 버겁게 느껴지실 수도 있어요. 집중 쪽만 살짝 볼게요.",
            ),
            AssessmentItem(
                self.instrument_id, "adhd_restless",
                "가만히 있기 어렵거나, 생각이 너무 빨리 넘어가 정리하기 힘드신가요?",
                ResponseType.LIKERT_0_3, SOFT,
                "정답은 없어요. 요즘 느낌에 가까운 쪽을 골라 주세요.",
            ),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        return _score(self.instrument_id, "adhd_", answers, 2)


class AlcoholProbeInstrument(AssessmentInstrument):
    instrument_id = "alcohol_probe"
    display_name = "음주 패턴 탐색 (AUDIT-C 정보제공형)"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem(
                self.instrument_id, "alc_freq",
                "스트레스를 풀기 위해 술을 찾는 날이 늘어난 느낌이 있으신가요?",
                ResponseType.LIKERT_0_3, SOFT,
                "비난하려는 게 아니에요. 몸과 마음을 돌보는 힌트로만 여쭤볼게요.",
            ),
            AssessmentItem(
                self.instrument_id, "alc_control",
                "한 번 마시면 생각보다 많이 마시게 되거나 후회한 적이 있으신가요?",
                ResponseType.LIKERT_0_3, SOFT,
                "편한 만큼만 답해 주셔도 괜찮아요.",
            ),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        return _score(self.instrument_id, "alc_", answers, 2)


class EatingProbeInstrument(AssessmentInstrument):
    instrument_id = "eating_probe"
    display_name = "식사·몸 이미지 탐색 (SCOFF 정보제공형)"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem(
                self.instrument_id, "eat_control",
                "먹는 양을 통제하기 어렵거나, 먹은 뒤 과도하게 걱정되는 때가 있으신가요?",
                ResponseType.LIKERT_0_3, SOFT,
                "몸·식사 이야기는 민감할 수 있어요. 부담되면 건너뛰셔도 됩니다.",
            ),
            AssessmentItem(
                self.instrument_id, "eat_body",
                "몸무게·체형이 마음에 크게 영향을 주나요?",
                ResponseType.LIKERT_0_3, SOFT,
                "자기비판 없이, 요즘 느끼는 정도만 알려 주세요.",
            ),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        return _score(self.instrument_id, "eat_", answers, 2)


class DissociationProbeInstrument(AssessmentInstrument):
    instrument_id = "dissociation_probe"
    display_name = "해리·거리감 탐색"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem(
                self.instrument_id, "dissoc_fog",
                "현실이 안개처럼 멀게 느껴지거나, 내가 나 같지 않은 순간이 있으셨나요?",
                ResponseType.LIKERT_0_3, SOFT,
                "요즘 감정이나 일에서 힘이 많이 드신 것 같아, 몸·의식 느낌도 살짝 여쭤볼게요.",
            ),
            AssessmentItem(
                self.instrument_id, "dissoc_blank",
                "시간이 비어 있거나 기억·감각이 뚝 끊긴 듯한 경험이 있으신가요?",
                ResponseType.LIKERT_0_3, SOFT,
                "무서운 질문이 아니에요. 있으셨다면 정도만 알려 주세요.",
            ),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        return _score(self.instrument_id, "dissoc_", answers, 2)


class SomaticProbeInstrument(AssessmentInstrument):
    instrument_id = "somatic_probe"
    display_name = "신체화·몸 신호 탐색"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem(
                self.instrument_id, "soma_body",
                "검사에서 큰 이상이 없어도 두통·가슴·배·근육 긴장이 자주 찾아오나요?",
                ResponseType.LIKERT_0_3, SOFT,
                "마음이 힘들 때 몸이 먼저 말하는 경우도 많아요. 편하게요.",
            ),
            AssessmentItem(
                self.instrument_id, "soma_worry",
                "몸 증상에 대한 걱정이 일상·관계에 영향을 주나요?",
                ResponseType.LIKERT_0_3, SOFT,
                "한 가지만 더 여쭤볼게요.",
            ),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        return _score(self.instrument_id, "soma_", answers, 2)


class AngerProbeInstrument(AssessmentInstrument):
    instrument_id = "anger_probe"
    display_name = "분노·과민 탐색"

    def items(self) -> List[AssessmentItem]:
        return [
            AssessmentItem(
                self.instrument_id, "anger_flash",
                "작은 일에도 화가 확 올라오거나 참기 어려웠던 적이 있으신가요?",
                ResponseType.LIKERT_0_3, SOFT,
                "제가 보기에 요즘 감정 에너지가 꽤 쓰이고 계신 것 같아요. 화의 느낌만 살짝요.",
            ),
            AssessmentItem(
                self.instrument_id, "anger_rel",
                "그 감정이 가까운 사람과의 관계에 영향을 준 적이 있으신가요?",
                ResponseType.LIKERT_0_3, SOFT,
                "비난이 아니에요. 관계 쪽 영향만 가볍게 볼게요.",
            ),
        ]

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        return _score(self.instrument_id, "anger_", answers, 2)


ABNORMAL_INSTRUMENTS = {
    "ocd_probe": OCDProbeInstrument(),
    "social_anxiety_probe": SocialAnxietyProbeInstrument(),
    "panic_probe": PanicProbeInstrument(),
    "mania_probe": ManiaProbeInstrument(),
    "adhd_probe": ADHDProbeInstrument(),
    "alcohol_probe": AlcoholProbeInstrument(),
    "eating_probe": EatingProbeInstrument(),
    "dissociation_probe": DissociationProbeInstrument(),
    "somatic_probe": SomaticProbeInstrument(),
    "anger_probe": AngerProbeInstrument(),
}
