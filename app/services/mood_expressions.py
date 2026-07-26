"""Granular facial-expression check-in → inferred 5-axis mood."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.mood_dimensions import (
    build_mood_portrait,
    composite_mood_score,
    normalize_dimensions,
)

EXPRESSION_DECK_VERSION = "1.0"
CATEGORY_ORDER = ("밝음", "평온", "무거움", "긴장", "지침", "복잡")

# dimensions map to valence / energy / anxiety / social / sleep (1–5)
MOOD_EXPRESSIONS: List[Dict[str, Any]] = [
    # —— 밝음 ——
    {
        "id": "beaming",
        "emoji": "😁",
        "label_ko": "환한 웃음",
        "category": "밝음",
        "hint_ko": "입이 벌어지고 눈이 반짝이는 표정",
        "guess_ko": "밝고 에너지가 올라와 있는 기분으로 보여요.",
        "dimensions": {"valence": 5, "energy": 5, "anxiety": 1, "social": 5, "sleep": 4},
    },
    {
        "id": "warm_smile",
        "emoji": "😊",
        "label_ko": "따뜻한 미소",
        "category": "밝음",
        "hint_ko": "입꼬리가 부드럽게 올라간 표정",
        "guess_ko": "기분 좋게 여유 있는 쪽에 가까워 보여요.",
        "dimensions": {"valence": 5, "energy": 4, "anxiety": 2, "social": 4, "sleep": 4},
    },
    {
        "id": "proud_grin",
        "emoji": "😌",
        "label_ko": "뿌듯한 미소",
        "category": "밝음",
        "hint_ko": "살짝 고개를 들고 만족스러운 표정",
        "guess_ko": "작은 성취감·자부심이 느껴지는 하루로 보여요.",
        "dimensions": {"valence": 4, "energy": 4, "anxiety": 2, "social": 3, "sleep": 4},
    },
    {
        "id": "playful",
        "emoji": "😜",
        "label_ko": "장난스러운",
        "category": "밝음",
        "hint_ko": "한쪽 눈 윙크·혀를 살짝 내민 표정",
        "guess_ko": "가볍고 장난기 있는 에너지로 보여요.",
        "dimensions": {"valence": 5, "energy": 5, "anxiety": 2, "social": 5, "sleep": 3},
    },
    {
        "id": "hopeful",
        "emoji": "🙂",
        "label_ko": "희망 찬",
        "category": "밝음",
        "hint_ko": "살짝 미소 지으며 앞을 보는 표정",
        "guess_ko": "괜찮은 편에, 앞으로 당기는 기분이 있어 보여요.",
        "dimensions": {"valence": 4, "energy": 4, "anxiety": 2, "social": 4, "sleep": 3},
    },
    {
        "id": "grateful",
        "emoji": "🥰",
        "label_ko": "감사·설렘",
        "category": "밝음",
        "hint_ko": "볼이 붉어지고 눈이 초승달처럼 접힌 표정",
        "guess_ko": "따뜻한 연결감·고마움이 큰 날로 보여요.",
        "dimensions": {"valence": 5, "energy": 4, "anxiety": 2, "social": 5, "sleep": 4},
    },
    # —— 평온 ——
    {
        "id": "soft_calm",
        "emoji": "😌",
        "label_ko": "부드러운 평온",
        "category": "평온",
        "hint_ko": "눈과 입이 편안히 풀린 표정",
        "guess_ko": "차분하고 안정된 기분으로 보여요.",
        "dimensions": {"valence": 4, "energy": 3, "anxiety": 1, "social": 3, "sleep": 4},
    },
    {
        "id": "quiet_ok",
        "emoji": "😐",
        "label_ko": "담담한 보통",
        "category": "평온",
        "hint_ko": "무표정에 가깝지만 편안한 얼굴",
        "guess_ko": "특별할 것 없는 보통 기분으로 보여요.",
        "dimensions": {"valence": 3, "energy": 3, "anxiety": 3, "social": 3, "sleep": 3},
    },
    {
        "id": "content",
        "emoji": "☺️",
        "label_ko": "만족한 고요",
        "category": "평온",
        "hint_ko": "눈을 살짝 감고 미소 짓는 표정",
        "guess_ko": "무리 없이 괜찮은, 고요한 만족감으로 보여요.",
        "dimensions": {"valence": 4, "energy": 3, "anxiety": 2, "social": 3, "sleep": 4},
    },
    {
        "id": "mindful",
        "emoji": "🧘",
        "label_ko": "집중·명상",
        "category": "평온",
        "hint_ko": "시선이 안으로 모인 고요한 표정",
        "guess_ko": "겉으로는 고요하지만 안쪽에 집중이 있어 보여요.",
        "dimensions": {"valence": 3, "energy": 3, "anxiety": 2, "social": 2, "sleep": 3},
    },
    {
        "id": "relieved",
        "emoji": "😮‍💨",
        "label_ko": "한숨 쉬는 안도",
        "category": "평온",
        "hint_ko": "긴장이 풀리며 숨을 내쉬는 표정",
        "guess_ko": "긴장이 조금 풀린 안도의 기색으로 보여요.",
        "dimensions": {"valence": 4, "energy": 2, "anxiety": 2, "social": 3, "sleep": 3},
    },
    # —— 무거움 ——
    {
        "id": "downcast",
        "emoji": "😔",
        "label_ko": "고개 숙인",
        "category": "무거움",
        "hint_ko": "시선이 아래로 내려간 표정",
        "guess_ko": "기분이 가라앉아 있는 쪽으로 보여요.",
        "dimensions": {"valence": 2, "energy": 2, "anxiety": 3, "social": 2, "sleep": 2},
    },
    {
        "id": "tearful",
        "emoji": "😢",
        "label_ko": "울컥한",
        "category": "무거움",
        "hint_ko": "눈가가 젖고 입술이 떨리는 표정",
        "guess_ko": "슬픔·서러움이 가까운 표정으로 보여요.",
        "dimensions": {"valence": 1, "energy": 2, "anxiety": 3, "social": 2, "sleep": 2},
    },
    {
        "id": "lonely",
        "emoji": "🥺",
        "label_ko": "쓸쓸한",
        "category": "무거움",
        "hint_ko": "눈이 커지고 입꼬리가 내려간 표정",
        "guess_ko": "외로움·허전함이 느껴지는 기분으로 보여요.",
        "dimensions": {"valence": 2, "energy": 2, "anxiety": 3, "social": 1, "sleep": 3},
    },
    {
        "id": "empty",
        "emoji": "😶",
        "label_ko": "멍·공허",
        "category": "무거움",
        "hint_ko": "표정이 거의 사라진 얼굴",
        "guess_ko": "감정 자체가 잘 안 잡히는 공허함으로 보여요.",
        "dimensions": {"valence": 2, "energy": 1, "anxiety": 2, "social": 2, "sleep": 2},
    },
    {
        "id": "heavy_sigh",
        "emoji": "😞",
        "label_ko": "한숨 섞인",
        "category": "무거움",
        "hint_ko": "입술을 내밀고 힘이 빠진 표정",
        "guess_ko": "마음이 무겁고 기운이 빠진 쪽으로 보여요.",
        "dimensions": {"valence": 2, "energy": 2, "anxiety": 3, "social": 2, "sleep": 2},
    },
    {
        "id": "heartbroken",
        "emoji": "💔",
        "label_ko": "가슴 아픈",
        "category": "무거움",
        "hint_ko": "눈물이 고이고 가슴을 누르는 듯한 표정",
        "guess_ko": "상실·상처가 가까운 무거운 기분으로 보여요.",
        "dimensions": {"valence": 1, "energy": 2, "anxiety": 4, "social": 1, "sleep": 2},
    },
    # —— 긴장 ——
    {
        "id": "worried",
        "emoji": "😟",
        "label_ko": "걱정 어린",
        "category": "긴장",
        "hint_ko": "이마에 주름이 잡힌 표정",
        "guess_ko": "걱정·긴장 신호가 조금 올라와 보여요.",
        "dimensions": {"valence": 2, "energy": 3, "anxiety": 4, "social": 3, "sleep": 2},
    },
    {
        "id": "anxious",
        "emoji": "😰",
        "label_ko": "식은땀",
        "category": "긴장",
        "hint_ko": "이마에 식은땀·눈이 커진 표정",
        "guess_ko": "불안이 꽤 올라와 있는 상태로 보여요.",
        "dimensions": {"valence": 2, "energy": 3, "anxiety": 5, "social": 2, "sleep": 2},
    },
    {
        "id": "fearful",
        "emoji": "😨",
        "label_ko": "겁먹은",
        "category": "긴장",
        "hint_ko": "눈이 크게 뜨이고 입이 벌어진 표정",
        "guess_ko": "두려움·경계가 높은 표정으로 보여요.",
        "dimensions": {"valence": 1, "energy": 4, "anxiety": 5, "social": 2, "sleep": 2},
    },
    {
        "id": "panic_edge",
        "emoji": "😱",
        "label_ko": "패닉 직전",
        "category": "긴장",
        "hint_ko": "얼굴이 굳고 숨이 가빠 보이는 표정",
        "guess_ko": "긴장이 한계에 가까운 상태로 보여요. 천천히 숨을 고르는 게 좋아요.",
        "dimensions": {"valence": 1, "energy": 4, "anxiety": 5, "social": 1, "sleep": 1},
    },
    {
        "id": "tense_jaw",
        "emoji": "😬",
        "label_ko": "이 악문",
        "category": "긴장",
        "hint_ko": "이를 악물고 입꼬리가 굳은 표정",
        "guess_ko": "억지로 버티는 긴장감이 있어 보여요.",
        "dimensions": {"valence": 2, "energy": 3, "anxiety": 4, "social": 2, "sleep": 2},
    },
    {
        "id": "overwhelmed",
        "emoji": "😵",
        "label_ko": "압도된",
        "category": "긴장",
        "hint_ko": "눈이 빙글 돌고 표정이 흐트러진 얼굴",
        "guess_ko": "할 일이 너무 많아 압도된 기분으로 보여요.",
        "dimensions": {"valence": 2, "energy": 2, "anxiety": 5, "social": 2, "sleep": 2},
    },
    # —— 지침 ——
    {
        "id": "sleepy",
        "emoji": "😴",
        "label_ko": "졸린",
        "category": "지침",
        "hint_ko": "눈이 감기고 고개가 기울어진 표정",
        "guess_ko": "수면·회복이 필요한 상태로 보여요.",
        "dimensions": {"valence": 3, "energy": 1, "anxiety": 2, "social": 2, "sleep": 1},
    },
    {
        "id": "drained",
        "emoji": "😩",
        "label_ko": "탈진",
        "category": "지침",
        "hint_ko": "눈을 가늘게 뜨고 한숨 쉬는 표정",
        "guess_ko": "에너지가 거의 바닥난 쪽으로 보여요.",
        "dimensions": {"valence": 2, "energy": 1, "anxiety": 3, "social": 2, "sleep": 1},
    },
    {
        "id": "yawning",
        "emoji": "🥱",
        "label_ko": "하품",
        "category": "지침",
        "hint_ko": "입을 크게 벌리며 하품하는 표정",
        "guess_ko": "몸이 쉬는 신호를 보내는 중으로 보여요.",
        "dimensions": {"valence": 3, "energy": 2, "anxiety": 2, "social": 3, "sleep": 2},
    },
    {
        "id": "foggy",
        "emoji": "😑",
        "label_ko": "멍한 피로",
        "category": "지침",
        "hint_ko": "시선이 초점을 잃은 표정",
        "guess_ko": "머리가 맑지 않은 피로감으로 보여요.",
        "dimensions": {"valence": 3, "energy": 2, "anxiety": 2, "social": 2, "sleep": 2},
    },
    {
        "id": "burnout",
        "emoji": "🫠",
        "label_ko": "녹아내리는",
        "category": "지침",
        "hint_ko": "얼굴이 녹아내리듯 힘이 빠진 표정",
        "guess_ko": "오래 버텨 온 번아웃 기색으로 보여요.",
        "dimensions": {"valence": 2, "energy": 1, "anxiety": 3, "social": 1, "sleep": 1},
    },
    # —— 복잡 ——
    {
        "id": "irritated",
        "emoji": "😤",
        "label_ko": "짜증 난",
        "category": "복잡",
        "hint_ko": "코로 숨을 내쉬며 찡그린 표정",
        "guess_ko": "짜증·열이 올라와 있는 기분으로 보여요.",
        "dimensions": {"valence": 2, "energy": 4, "anxiety": 4, "social": 2, "sleep": 3},
    },
    {
        "id": "angry",
        "emoji": "😠",
        "label_ko": "화난",
        "category": "복잡",
        "hint_ko": "눈썹이 모이고 입이 굳은 표정",
        "guess_ko": "화가 가까운 상태로 보여요. 억누르지 않아도 괜찮아요.",
        "dimensions": {"valence": 2, "energy": 5, "anxiety": 4, "social": 2, "sleep": 3},
    },
    {
        "id": "resentful",
        "emoji": "😒",
        "label_ko": "억울·삐친",
        "category": "복잡",
        "hint_ko": "한쪽 눈썹을 치켜올린 표정",
        "guess_ko": "억울함·서운함이 섞인 표정으로 보여요.",
        "dimensions": {"valence": 2, "energy": 3, "anxiety": 3, "social": 2, "sleep": 3},
    },
    {
        "id": "confused",
        "emoji": "😕",
        "label_ko": "헷갈리는",
        "category": "복잡",
        "hint_ko": "눈썹이 한쪽으로 기울어진 표정",
        "guess_ko": "생각이 정리되지 않은 혼란감으로 보여요.",
        "dimensions": {"valence": 3, "energy": 2, "anxiety": 4, "social": 2, "sleep": 3},
    },
    {
        "id": "ambivalent",
        "emoji": "😶‍🌫️",
        "label_ko": "양가감정",
        "category": "복잡",
        "hint_ko": "웃는 듯 마는 듯 애매한 표정",
        "guess_ko": "좋음과 힘듦이 한꺼번에 있는 날로 보여요.",
        "dimensions": {"valence": 3, "energy": 3, "anxiety": 3, "social": 3, "sleep": 3},
    },
    {
        "id": "masking",
        "emoji": "🙂‍↔️",
        "label_ko": "괜찮은 척",
        "category": "복잡",
        "hint_ko": "겉미소와 눈빛이 어긋난 표정",
        "guess_ko": "겉으로는 괜찮은 척하지만 안이 무거울 수 있어요.",
        "dimensions": {"valence": 3, "energy": 3, "anxiety": 4, "social": 4, "sleep": 2},
    },
    {
        "id": "shy",
        "emoji": "😳",
        "label_ko": "수줍·당황",
        "category": "복잡",
        "hint_ko": "볼이 붉어지고 시선을 피하는 표정",
        "guess_ko": "당황·수줍음이 섞인 긴장으로 보여요.",
        "dimensions": {"valence": 3, "energy": 3, "anxiety": 4, "social": 2, "sleep": 3},
    },
    {
        "id": "curious",
        "emoji": "🤔",
        "label_ko": "호기심",
        "category": "복잡",
        "hint_ko": "턱을 괴고 생각하는 표정",
        "guess_ko": "탐색·궁금함이 살아있는 기분으로 보여요.",
        "dimensions": {"valence": 4, "energy": 3, "anxiety": 2, "social": 3, "sleep": 3},
    },
]

_BY_ID: Dict[str, Dict[str, Any]] = {row["id"]: row for row in MOOD_EXPRESSIONS}


def get_expression(expression_id: str) -> Optional[Dict[str, Any]]:
    return _BY_ID.get((expression_id or "").strip())


def list_expressions() -> List[Dict[str, Any]]:
    return [dict(row) for row in MOOD_EXPRESSIONS]


def expression_deck_payload() -> Dict[str, Any]:
    return {
        "version": EXPRESSION_DECK_VERSION,
        "total": len(MOOD_EXPRESSIONS),
        "categories": list(CATEGORY_ORDER),
        "guide_ko": (
            "지금 얼굴에 가까운 표정을 골라 주세요. "
            "선택한 표정으로 오늘의 기분을 추측해 5축으로 맞춰 드려요."
        ),
        "expressions": list_expressions(),
    }


def infer_mood_from_expression(expression_id: str) -> Dict[str, Any]:
    """Map a facial expression pick → dimensions + human-readable guess."""
    item = get_expression(expression_id)
    if not item:
        raise KeyError(f"unknown expression_id: {expression_id}")
    dims = normalize_dimensions(item["dimensions"])
    portrait = build_mood_portrait(dims)
    score = composite_mood_score(dims)
    return {
        "expression_id": item["id"],
        "emoji": item["emoji"],
        "label_ko": item["label_ko"],
        "category": item["category"],
        "hint_ko": item["hint_ko"],
        "guess_ko": item["guess_ko"],
        "dimensions": dims,
        "mood_score": score,
        "mood_portrait": portrait,
        "inferred": True,
    }


def enrich_checkin_with_expression(payload: Dict[str, Any], expression_id: Optional[str]) -> Dict[str, Any]:
    if not expression_id:
        return payload
    try:
        inferred = infer_mood_from_expression(expression_id)
    except KeyError:
        return payload
    out = dict(payload)
    out["expression_id"] = inferred["expression_id"]
    out["expression"] = {
        "id": inferred["expression_id"],
        "emoji": inferred["emoji"],
        "label_ko": inferred["label_ko"],
        "category": inferred["category"],
        "guess_ko": inferred["guess_ko"],
    }
    return out
