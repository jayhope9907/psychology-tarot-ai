"""Classic Rider–Waite tarot rules for multi-card spreads."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

DEFAULT_SPREAD = "five_card"
THREE_CARD_COUNT = 3
FIVE_CARD_COUNT = 5
SEVEN_CARD_COUNT = 7
REVERSE_CHANCE = 0.5

THREE_CARD_POSITIONS: List[Dict[str, str]] = [
    {
        "id": "past",
        "label_ko": "과거·뿌리",
        "guide_ko": "과거의 뿌리·배경·무엇이 지금의 마음을 만들었는지",
        "ask_ko": "무엇이 여기까지 이끌었나요?",
    },
    {
        "id": "present",
        "label_ko": "현재·핵심",
        "guide_ko": "지금 상황의 핵심·현재 감정·직면하고 있는 것",
        "ask_ko": "지금 가장 크게 느껴지는 것은?",
    },
    {
        "id": "future",
        "label_ko": "미래·방향",
        "guide_ko": "앞으로의 방향·가능성·가볍게 열어둘 다음 한 걸음",
        "ask_ko": "열어둘 다음 한 걸음은?",
    },
]

FIVE_CARD_POSITIONS: List[Dict[str, str]] = [
    {
        "id": "situation",
        "label_ko": "상황",
        "guide_ko": "지금 마주한 장면·맥락",
        "ask_ko": "지금 어떤 장면 안에 있나요?",
    },
    {
        "id": "challenge",
        "label_ko": "도전",
        "guide_ko": "가로막는 긴장·마찰·부담",
        "ask_ko": "무엇이 가장 걸리나요?",
    },
    {
        "id": "hidden",
        "label_ko": "숨은 마음",
        "guide_ko": "아직 말로 안 나온 마음·무의식의 결",
        "ask_ko": "겉으로 안 보이는 마음은?",
    },
    {
        "id": "advice",
        "label_ko": "조언",
        "guide_ko": "부담 없이 시도할 수 있는 태도·작은 선택",
        "ask_ko": "오늘 가능한 작은 선택은?",
    },
    {
        "id": "flow",
        "label_ko": "흐름",
        "guide_ko": "열어둘 가능성·에너지의 방향 (예언 아님)",
        "ask_ko": "어떤 흐름을 열어둘까요?",
    },
]

SEVEN_CARD_POSITIONS: List[Dict[str, str]] = [
    {
        "id": "past",
        "label_ko": "과거·뿌리",
        "guide_ko": "지금의 마음을 만든 경험·배경",
        "ask_ko": "무엇이 여기까지 이끌었나요?",
    },
    {
        "id": "present",
        "label_ko": "현재·핵심",
        "guide_ko": "지금 가장 또렷한 감정·상황",
        "ask_ko": "지금 가장 크게 느껴지는 것은?",
    },
    {
        "id": "hidden",
        "label_ko": "숨은 영향",
        "guide_ko": "잘 안 보이지만 영향을 주는 결",
        "ask_ko": "보이지 않는 영향은?",
    },
    {
        "id": "advice",
        "label_ko": "조언",
        "guide_ko": "지금 도움이 되는 태도·작은 행동",
        "ask_ko": "무엇을 가볍게 시도해볼까요?",
    },
    {
        "id": "environment",
        "label_ko": "환경·관계",
        "guide_ko": "주변 사람·상황·지지 또는 압력",
        "ask_ko": "주변은 어떻게 작용하나요?",
    },
    {
        "id": "hope_fear",
        "label_ko": "희망·두려움",
        "guide_ko": "바라는 것과 걱정이 만나는 자리",
        "ask_ko": "무엇을 바라고, 무엇을 두려워하나요?",
    },
    {
        "id": "direction",
        "label_ko": "방향",
        "guide_ko": "열어둘 다음 한 걸음의 가능성",
        "ask_ko": "다음으로 열어둘 방향은?",
    },
]

SPREAD_DEFS: Dict[str, Dict[str, Any]] = {
    "three_card": {
        "label_ko": "3카드 · 과거·현재·미래",
        "count": THREE_CARD_COUNT,
        "positions": THREE_CARD_POSITIONS,
    },
    "five_card": {
        "label_ko": "5카드 · 상황·도전·숨은 마음·조언·흐름",
        "count": FIVE_CARD_COUNT,
        "positions": FIVE_CARD_POSITIONS,
    },
    "seven_card": {
        "label_ko": "7카드 · 깊은 자기성찰",
        "count": SEVEN_CARD_COUNT,
        "positions": SEVEN_CARD_POSITIONS,
    },
}

ALLOWED_SPREADS = tuple(SPREAD_DEFS.keys())

_ALL_POSITIONS: List[Dict[str, str]] = (
    THREE_CARD_POSITIONS + FIVE_CARD_POSITIONS + SEVEN_CARD_POSITIONS
)
_POSITION_BY_LABEL: Dict[str, Dict[str, str]] = {
    pos["label_ko"]: pos for pos in _ALL_POSITIONS
}

SUIT_RULES: Dict[str, Dict[str, str]] = {
    "wands": {
        "label_ko": "지팡이",
        "element_ko": "불",
        "domain_ko": "의욕·실행·에너지·창의",
        "reading_ko": "행동·추진·열정이 주제일 때 더 또렷해져요.",
    },
    "cups": {
        "label_ko": "컵",
        "element_ko": "물",
        "domain_ko": "감정·관계·수용·직관",
        "reading_ko": "마음·교감·관계의 결이 주제일 때 더 또렷해져요.",
    },
    "swords": {
        "label_ko": "검",
        "element_ko": "공기",
        "domain_ko": "사고·경계·진실·갈등",
        "reading_ko": "생각·결정·말·갈등이 주제일 때 더 또렷해져요.",
    },
    "pentacles": {
        "label_ko": "펜타클",
        "element_ko": "흙",
        "domain_ko": "생활·몸·일·안정·돌봄",
        "reading_ko": "현실·자원·루틴·안정이 주제일 때 더 또렷해져요.",
    },
}

RANK_RULES: Dict[str, Dict[str, str]] = {
    "ace": {"label_ko": "에이스", "guide_ko": "시작·씨앗·새로운 가능성"},
    "two": {"label_ko": "2", "guide_ko": "선택·균형·둘 사이의 긴장"},
    "three": {"label_ko": "3", "guide_ko": "확장·협력·첫 결실"},
    "four": {"label_ko": "4", "guide_ko": "안정·구조·잠시 멈춤"},
    "five": {"label_ko": "5", "guide_ko": "갈등·상실·마찰"},
    "six": {"label_ko": "6", "guide_ko": "회복·이동·조화로의 복귀"},
    "seven": {"label_ko": "7", "guide_ko": "시험·인내·전략"},
    "eight": {"label_ko": "8", "guide_ko": "집중·숙련·빠른 전개"},
    "nine": {"label_ko": "9", "guide_ko": "거의 완성·혼자 버티기·긴장"},
    "ten": {"label_ko": "10", "guide_ko": "완성·과부하·한 사이클의 끝"},
    "page": {"label_ko": "시종", "guide_ko": "소식·배움·호기심·초보 에너지"},
    "knight": {"label_ko": "기사", "guide_ko": "추진·이동·몰입·한쪽으로 치우침"},
    "queen": {"label_ko": "여왕", "guide_ko": "성숙한 수용·돌봄·내적 숙련"},
    "king": {"label_ko": "왕", "guide_ko": "책임·통솔·바깥으로 드러난 숙련"},
}

ORIENTATION_RULES = {
    "upright": {
        "label_ko": "정방향",
        "guide_ko": "에너지가 비교적 열리고 표현되기 쉬운 상태",
    },
    "reversed": {
        "label_ko": "역방향",
        "guide_ko": "막힘·내면화·과잉·시기가 아직 아님 — 운명 단정 금지",
    },
}

ARCANA_RULES = {
    "major": {
        "label_ko": "메이저 아르카나",
        "guide_ko": "큰 테마·전환점·삶의 큰 흐름을 가볍게 비춤",
    },
    "minor": {
        "label_ko": "마이너 아르카나",
        "guide_ko": "일상·감정·생각·현실의 구체적 결을 비춤",
    },
}

PRACTICE_RULES_KO = [
    "스프레드는 3·5·7장 중 고릅니다. 각 카드는 자기 위치로만 읽습니다.",
    "덱은 78장(메이저 22 + 마이너 56)이며, 중복 없이 뽑습니다.",
    "섞은 뒤 뒷면만 보고 직감으로 고릅니다. 앞면을 보고 고르지 않습니다.",
    "정방향/역방향은 카드마다 독립적으로 공정하게 결정됩니다.",
    "미래·흐름·방향은 예언이 아니라 가능성입니다.",
    "메이저는 큰 테마, 마이너(수트·원소)는 일상의 결로 읽습니다.",
    "궁정 카드(시종·기사·여왕·왕)는 사람·태도·접근 방식으로 가볍게 봅니다.",
    "진단·운명·확정 예언으로 쓰지 않습니다. 자기성찰 거울입니다.",
]


def normalize_spread(
    spread: Optional[str] = None,
    count: Optional[int] = None,
) -> Tuple[str, int]:
    """Resolve spread id + card count. Defaults to five_card."""
    key = (spread or "").strip() or DEFAULT_SPREAD
    if key == "single":
        key = "three_card"
    if key not in SPREAD_DEFS:
        if count == THREE_CARD_COUNT:
            key = "three_card"
        elif count == SEVEN_CARD_COUNT:
            key = "seven_card"
        elif count == FIVE_CARD_COUNT:
            key = "five_card"
        else:
            key = DEFAULT_SPREAD
    return key, int(SPREAD_DEFS[key]["count"])


def normalize_three_card_spread(
    spread: Optional[str] = None,
    count: Optional[int] = None,
) -> Tuple[str, int]:
    """Backward-compatible alias — now resolves any allowed spread."""
    return normalize_spread(spread, count)


def positions_for_spread(spread: str) -> List[Dict[str, str]]:
    key, _ = normalize_spread(spread)
    return list(SPREAD_DEFS[key]["positions"])


def enrich_card_rules(card: Dict[str, Any]) -> Dict[str, Any]:
    """Attach classic reading metadata to a drawn card."""
    out = dict(card)
    arcana = out.get("arcana") or ("minor" if out.get("suit") else "major")
    suit = out.get("suit")
    rank = out.get("rank")
    reversed_card = bool(out.get("reversed"))

    out["arcana"] = arcana
    out["arcana_rule"] = ARCANA_RULES.get(arcana, ARCANA_RULES["major"])
    out["orientation_rule"] = (
        ORIENTATION_RULES["reversed"] if reversed_card else ORIENTATION_RULES["upright"]
    )
    if suit and suit in SUIT_RULES:
        out["suit_rule"] = SUIT_RULES[suit]
    if rank and rank in RANK_RULES:
        out["rank_rule"] = RANK_RULES[rank]

    position = out.get("position") or ""
    pos = _POSITION_BY_LABEL.get(position)
    if pos:
        out["position_id"] = pos["id"]
        out["position_guide"] = pos["guide_ko"]
        out["position_ask"] = pos["ask_ko"]
    return out


def rules_manifest(spread: Optional[str] = None) -> Dict[str, Any]:
    key, count = normalize_spread(spread)
    positions = positions_for_spread(key)
    return {
        "system": "rider_waite",
        "spread": key,
        "count": count,
        "default_spread": DEFAULT_SPREAD,
        "available_spreads": {
            sid: {
                "label_ko": meta["label_ko"],
                "count": meta["count"],
                "positions": meta["positions"],
            }
            for sid, meta in SPREAD_DEFS.items()
        },
        "reverse_chance": REVERSE_CHANCE,
        "deck": {"total": 78, "major": 22, "minor": 56},
        "positions": positions,
        "suits": SUIT_RULES,
        "ranks": RANK_RULES,
        "orientations": ORIENTATION_RULES,
        "arcana": ARCANA_RULES,
        "practice_ko": PRACTICE_RULES_KO,
        "disclaimer_ko": "교육·자기성찰용이며 점술·진단·확정 예언이 아닙니다.",
    }


def narrative_rules_block(spread: Optional[str] = None) -> str:
    key, count = normalize_spread(spread)
    label = SPREAD_DEFS[key]["label_ko"]
    lines = [f"## 클래식 타로 규칙 (필수) · {label} ({count}장)"]
    for item in PRACTICE_RULES_KO:
        lines.append(f"- {item}")
    lines.append("- 수트: 지팡이(불)·컵(물)·검(공기)·펜타클(흙)")
    lines.append("- 정방향=열림/표현, 역방향=막힘/내면화/과잉 (단정 금지)")
    return "\n".join(lines)


def position_summary_lines(cards: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for card in cards:
        enriched = enrich_card_rules(card)
        orientation = "역방향" if enriched.get("reversed") else "정방향"
        suit_bit = ""
        if enriched.get("suit_rule"):
            sr = enriched["suit_rule"]
            suit_bit = f" · {sr['label_ko']}/{sr['element_ko']}"
        rank_bit = ""
        if enriched.get("rank_rule"):
            rank_bit = f" · {enriched['rank_rule']['label_ko']}"
        lines.append(
            f"{enriched.get('position', '')}({enriched.get('position_guide', '')}): "
            f"{enriched.get('name_ko')} ({orientation}"
            f"{' · 메이저' if enriched.get('arcana') == 'major' else suit_bit}{rank_bit})"
        )
    return lines
