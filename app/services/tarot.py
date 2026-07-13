from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

_DECK_PATH = Path(__file__).resolve().parent.parent / "data" / "tarot_deck.json"
_MINOR_PATH = Path(__file__).resolve().parent.parent / "data" / "minor_arcana.json"
_DECK_CACHE: Optional[Dict[str, Any]] = None
_MINOR_CACHE: Optional[List[Dict[str, Any]]] = None
_FULL_DECK_CACHE: Optional[List[Dict[str, Any]]] = None

# Classic Rider–Waite 3-card: past / present / future. Reversal is fair coin flip.
DEFAULT_SPREAD = "three_card"
THREE_CARD_COUNT = 3
REVERSE_CHANCE = 0.5
THREE_CARD_POSITION_GUIDE = (
    ("과거·뿌리", "과거의 뿌리·배경·무엇이 지금의 마음을 만들었는지"),
    ("현재·핵심", "지금 상황의 핵심·현재 감정·직면하고 있는 것"),
    ("미래·방향", "앞으로의 방향·가능성·가볍게 열어둘 다음 한 걸음"),
)

# Rider–Waite Major Arcana (public domain, Wikimedia Commons)
_TAROT_IMAGE_PATHS: Dict[str, str] = {
    "fool": "9/90/RWS_Tarot_00_Fool.jpg",
    "magician": "d/de/RWS_Tarot_01_Magician.jpg",
    "high_priestess": "8/88/RWS_Tarot_02_High_Priestess.jpg",
    "empress": "d/d2/RWS_Tarot_03_Empress.jpg",
    "emperor": "c/c3/RWS_Tarot_04_Emperor.jpg",
    "hierophant": "8/8d/RWS_Tarot_05_Hierophant.jpg",
    "lovers": "3/3a/RWS_Tarot_06_Lovers.jpg",
    "chariot": "9/9b/RWS_Tarot_07_Chariot.jpg",
    "strength": "f/f5/RWS_Tarot_08_Strength.jpg",
    "hermit": "4/4d/RWS_Tarot_09_Hermit.jpg",
    "wheel_of_fortune": "3/3c/RWS_Tarot_10_Wheel_of_Fortune.jpg",
    "justice": "e/e0/RWS_Tarot_11_Justice.jpg",
    "hanged_man": "2/2b/RWS_Tarot_12_Hanged_Man.jpg",
    "death": "d/d7/RWS_Tarot_13_Death.jpg",
    "temperance": "f/f8/RWS_Tarot_14_Temperance.jpg",
    "devil": "5/55/RWS_Tarot_15_Devil.jpg",
    "tower": "5/53/RWS_Tarot_16_Tower.jpg",
    "star": "d/db/RWS_Tarot_17_Star.jpg",
    "moon": "7/7f/RWS_Tarot_18_Moon.jpg",
    "sun": "1/17/RWS_Tarot_19_Sun.jpg",
    "judgement": "d/dd/RWS_Tarot_20_Judgement.jpg",
    "world": "f/ff/RWS_Tarot_21_World.jpg",
}


def card_image_url(card_id: str, image_file: Optional[str] = None) -> str:
    path = _TAROT_IMAGE_PATHS.get(card_id)
    if path:
        return f"https://upload.wikimedia.org/wikipedia/commons/{path}"
    if image_file:
        digest = hashlib.md5(image_file.encode()).hexdigest()
        return f"https://upload.wikimedia.org/wikipedia/commons/{digest[0]}/{digest[:2]}/{image_file}"
    return ""


def _load_deck() -> Dict[str, Any]:
    global _DECK_CACHE
    if _DECK_CACHE is None:
        with _DECK_PATH.open(encoding="utf-8") as handle:
            _DECK_CACHE = json.load(handle)
    return _DECK_CACHE


def get_major_arcana() -> List[Dict[str, Any]]:
    return [dict(card, arcana="major") for card in _load_deck()["major_arcana"]]


def get_minor_arcana() -> List[Dict[str, Any]]:
    global _MINOR_CACHE
    if _MINOR_CACHE is None:
        with _MINOR_PATH.open(encoding="utf-8") as handle:
            _MINOR_CACHE = json.load(handle)
    return [dict(card) for card in _MINOR_CACHE]


def get_full_deck() -> List[Dict[str, Any]]:
    global _FULL_DECK_CACHE
    if _FULL_DECK_CACHE is None:
        _FULL_DECK_CACHE = get_major_arcana() + get_minor_arcana()
    return [dict(card) for card in _FULL_DECK_CACHE]


def get_card_by_id(card_id: str) -> Optional[Dict[str, Any]]:
    for card in get_full_deck():
        if card["id"] == card_id:
            return dict(card)
    return None


def get_card_by_name(name: str) -> Optional[Dict[str, Any]]:
    normalized = (name or "").strip().lower()
    for card in get_full_deck():
        if card["name_en"].lower() == normalized or card["name_ko"] == name:
            return dict(card)
    return None


def build_archetype_map() -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    for card in get_full_deck():
        mapping[card["name_en"]] = {
            "archetype": card["archetype"],
            "psychiatric_stress_weight": card["psychiatric_stress_weight"],
            "cognitive_distortion_flag": card["cognitive_distortion_flag"],
            "attachment_matrix_score": card["attachment_matrix_score"],
        }
    return mapping


TAROT_ARCHETYPE_MAP = build_archetype_map()


def _catalog_entry(card: Dict[str, Any]) -> Dict[str, Any]:
    image_file = card.get("image_file")
    return {
        "id": card["id"],
        "number": card["number"],
        "arcana": card.get("arcana", "major"),
        "suit": card.get("suit"),
        "rank": card.get("rank"),
        "name_en": card["name_en"],
        "name_ko": card["name_ko"],
        "symbol": card["symbol"],
        "keywords_ko": card["keywords_ko"],
        "gradient": card["gradient"],
        "image_url": card_image_url(card["id"], image_file),
        "upright_ko": card["upright_ko"],
        "reversed_ko": card["reversed_ko"],
        "psychology_theme": card["psychology_theme"],
    }


def list_deck_catalog() -> Dict[str, Any]:
    cards = [_catalog_entry(card) for card in get_full_deck()]
    return {
        "cards": cards,
        "spreads": _load_deck()["spreads"],
        "total": len(cards),
        "major_count": len(get_major_arcana()),
        "minor_count": len(get_minor_arcana()),
    }


def normalize_three_card_spread(spread: Optional[str] = None, count: Optional[int] = None) -> tuple[str, int]:
    """Consumer tarot is locked to the classic 3-card spread."""
    return DEFAULT_SPREAD, THREE_CARD_COUNT


def _is_reversed(rng: random.Random | None = None) -> bool:
    if rng is None:
        return random.random() < REVERSE_CHANCE
    return rng.random() < REVERSE_CHANCE


def build_draw_from_picks(
    card_ids: List[str],
    spread: str = DEFAULT_SPREAD,
    reversed_flags: Optional[List[bool]] = None,
) -> Dict[str, Any]:
    spread, _ = normalize_three_card_spread(spread, len(card_ids))
    spread_meta = _load_deck()["spreads"].get(spread) or _load_deck()["spreads"][DEFAULT_SPREAD]
    positions = spread_meta["positions"]
    drawn: List[Dict[str, Any]] = []

    # Without-replacement: first occurrence wins if duplicates slipped in.
    seen: set[str] = set()
    ordered_ids: List[str] = []
    for card_id in card_ids:
        if card_id in seen:
            continue
        seen.add(card_id)
        ordered_ids.append(card_id)

    for index, card_id in enumerate(ordered_ids[:THREE_CARD_COUNT]):
        card = get_card_by_id(card_id)
        if not card:
            continue
        reversed_card = (
            reversed_flags[index]
            if reversed_flags and index < len(reversed_flags)
            else _is_reversed()
        )
        position = positions[index] if index < len(positions) else f"카드 {index + 1}"
        drawn.append(
            {
                "id": card["id"],
                "number": card["number"],
                "arcana": card.get("arcana", "major"),
                "suit": card.get("suit"),
                "rank": card.get("rank"),
                "name_en": card["name_en"],
                "name_ko": card["name_ko"],
                "symbol": card["symbol"],
                "keywords_ko": card["keywords_ko"],
                "gradient": card["gradient"],
                "image_url": card_image_url(card["id"], card.get("image_file")),
                "position": position,
                "reversed": reversed_card,
                "meaning_ko": card["reversed_ko"] if reversed_card else card["upright_ko"],
                "psychology_theme": card["psychology_theme"],
                "archetype": card["archetype"],
            }
        )

    return {
        "spread": spread,
        "spread_label_ko": spread_meta["label_ko"],
        "positions": positions[: len(drawn)],
        "cards": drawn,
        "rules": {
            "spread": DEFAULT_SPREAD,
            "count": THREE_CARD_COUNT,
            "reverse_chance": REVERSE_CHANCE,
            "positions": [
                {"label": label, "guide_ko": guide} for label, guide in THREE_CARD_POSITION_GUIDE
            ],
        },
    }


def draw_cards(
    count: int = THREE_CARD_COUNT,
    spread: str = DEFAULT_SPREAD,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    deck = get_full_deck()
    spread, draw_count = normalize_three_card_spread(spread, count)
    spread_meta = _load_deck()["spreads"].get(spread) or _load_deck()["spreads"][DEFAULT_SPREAD]
    positions = spread_meta["positions"]
    draw_count = min(draw_count, len(deck), len(positions))

    rng = random.Random(seed)
    picked = rng.sample(deck, draw_count)

    drawn: List[Dict[str, Any]] = []
    for index, card in enumerate(picked):
        reversed_card = _is_reversed(rng)
        position = positions[index] if index < len(positions) else f"카드 {index + 1}"
        drawn.append(
            {
                "id": card["id"],
                "number": card["number"],
                "arcana": card.get("arcana", "major"),
                "suit": card.get("suit"),
                "rank": card.get("rank"),
                "name_en": card["name_en"],
                "name_ko": card["name_ko"],
                "symbol": card["symbol"],
                "keywords_ko": card["keywords_ko"],
                "gradient": card["gradient"],
                "image_url": card_image_url(card["id"], card.get("image_file")),
                "position": position,
                "reversed": reversed_card,
                "meaning_ko": card["reversed_ko"] if reversed_card else card["upright_ko"],
                "psychology_theme": card["psychology_theme"],
                "archetype": card["archetype"],
            }
        )

    return {
        "spread": spread,
        "spread_label_ko": spread_meta["label_ko"],
        "positions": positions[:draw_count],
        "cards": drawn,
        "rules": {
            "spread": DEFAULT_SPREAD,
            "count": THREE_CARD_COUNT,
            "reverse_chance": REVERSE_CHANCE,
            "positions": [
                {"label": label, "guide_ko": guide} for label, guide in THREE_CARD_POSITION_GUIDE
            ],
        },
    }


def build_local_reading(user_story: str, draw_result: Dict[str, Any]) -> Dict[str, Any]:
    cards = draw_result.get("cards") or []
    card_lines: List[Dict[str, str]] = []
    themes: List[str] = []
    guide_by_label = {label: guide for label, guide in THREE_CARD_POSITION_GUIDE}

    for card in cards:
        orientation = "역방향" if card.get("reversed") else "정방향"
        position = card.get("position", "")
        card_lines.append(
            {
                "position": position,
                "position_guide": guide_by_label.get(position, ""),
                "title": f"{card['name_ko']} ({card['name_en']}) · {orientation}",
                "meaning": card.get("meaning_ko", ""),
                "psychology_theme": card.get("psychology_theme", ""),
                "archetype": card.get("archetype", ""),
            }
        )
        if card.get("psychology_theme"):
            themes.append(card["psychology_theme"])

    summary_parts = [
        "클래식 3카드(과거·현재·미래) 규칙으로 읽어요. 카드는 지금 마음을 살짝 비추는 거울이에요.",
    ]
    if user_story.strip():
        summary_parts.append("적어 주신 상황을 바탕으로, 부담 없이 읽을 수 있게 정리했어요.")
    for card in cards:
        pos = card.get("position", "")
        guide = guide_by_label.get(pos, pos)
        orientation = "역방향" if card.get("reversed") else "정방향"
        summary_parts.append(
            f"{pos}({guide})에는 '{card.get('name_ko', '')}'({orientation})가 놓였어요."
        )

    cbt_actions = [
        "과거·뿌리 카드가 건드린 배경을 한 줄로 적어 보세요.",
        "현재·핵심에서 오늘 할 수 있는 작은 행동 하나만 정해 보세요.",
        "미래·방향은 확정이 아니라 가능성 — 부담 없는 다음 한 걸음만 열어 두세요.",
    ]
    if "직장" in user_story or "회사" in user_story:
        cbt_actions[1] = "직장에서 통제 가능한 작은 한 가지를 정해 실천해 보세요."

    primary = cards[1] if len(cards) > 1 else (cards[0] if cards else {})

    return {
        "summary": " ".join(summary_parts),
        "cards": card_lines,
        "psychology_themes": themes,
        "cbt_actions": cbt_actions,
        "primary_card": primary.get("name_en", "The Fool"),
        "reading_tone": "three_card_classic",
        "spread_rules_ko": [f"{label}: {guide}" for label, guide in THREE_CARD_POSITION_GUIDE],
    }


def format_draw_for_prompt(draw_result: Dict[str, Any]) -> str:
    guide_by_label = {label: guide for label, guide in THREE_CARD_POSITION_GUIDE}
    lines: List[str] = [
        "스프레드: 3카드 (과거·뿌리 → 현재·핵심 → 미래·방향)",
        "규칙: 정방향/역방향 각 카드 독립, 중복 없이 3장, 위치별 의미로만 가볍게 연결",
    ]
    for card in draw_result.get("cards") or []:
        orientation = "역방향" if card.get("reversed") else "정방향"
        position = card.get("position", "카드")
        guide = guide_by_label.get(position, "")
        arcana = "메이저" if card.get("arcana") == "major" else f"마이너({card.get('suit') or '-'})"
        lines.append(
            f"- [{position}] ({guide}) · {card.get('name_ko')} / {orientation} / {arcana} — "
            f"{card.get('meaning_ko', '')} · 테마: {card.get('psychology_theme', '')} · "
            f"원형: {card.get('archetype', '')}"
        )
    return "\n".join(lines) if len(lines) > 2 else "- (카드 없음)"


def merge_reading_with_output(local: Dict[str, Any], therapy_output: Dict[str, Any]) -> Dict[str, Any]:
    analysis = (
        therapy_output.get("analysis")
        or therapy_output.get("assistant_message")
        or therapy_output.get("summary")
        or ""
    )
    return {
        **local,
        "ai_analysis": analysis,
        "psychiatric_feature_profile": therapy_output.get("psychiatric_feature_profile"),
        "recommended_actions": (
            therapy_output.get("recommended_actions")
            or therapy_output.get("actions")
            or local.get("cbt_actions")
        ),
    }
