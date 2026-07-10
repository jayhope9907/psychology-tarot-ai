from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

_DECK_PATH = Path(__file__).resolve().parent.parent / "data" / "tarot_deck.json"
_DECK_CACHE: Optional[Dict[str, Any]] = None


def _load_deck() -> Dict[str, Any]:
    global _DECK_CACHE
    if _DECK_CACHE is None:
        with _DECK_PATH.open(encoding="utf-8") as handle:
            _DECK_CACHE = json.load(handle)
    return _DECK_CACHE


def get_major_arcana() -> List[Dict[str, Any]]:
    return list(_load_deck()["major_arcana"])


def get_card_by_id(card_id: str) -> Optional[Dict[str, Any]]:
    for card in get_major_arcana():
        if card["id"] == card_id:
            return dict(card)
    return None


def get_card_by_name(name: str) -> Optional[Dict[str, Any]]:
    normalized = (name or "").strip().lower()
    for card in get_major_arcana():
        if card["name_en"].lower() == normalized or card["name_ko"] == name:
            return dict(card)
    return None


def build_archetype_map() -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    for card in get_major_arcana():
        mapping[card["name_en"]] = {
            "archetype": card["archetype"],
            "psychiatric_stress_weight": card["psychiatric_stress_weight"],
            "cognitive_distortion_flag": card["cognitive_distortion_flag"],
            "attachment_matrix_score": card["attachment_matrix_score"],
        }
    return mapping


TAROT_ARCHETYPE_MAP = build_archetype_map()


def list_deck_catalog() -> Dict[str, Any]:
    cards = []
    for card in get_major_arcana():
        cards.append(
            {
                "id": card["id"],
                "number": card["number"],
                "name_en": card["name_en"],
                "name_ko": card["name_ko"],
                "symbol": card["symbol"],
                "keywords_ko": card["keywords_ko"],
                "gradient": card["gradient"],
            }
        )
    return {"cards": cards, "spreads": _load_deck()["spreads"]}


def draw_cards(
    count: int = 3,
    spread: str = "three_card",
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    deck = get_major_arcana()
    spread_meta = _load_deck()["spreads"].get(spread) or _load_deck()["spreads"]["three_card"]
    positions = spread_meta["positions"]
    draw_count = min(max(count, 1), len(deck), len(positions) if spread != "single" else count)

    rng = random.Random(seed)
    picked = rng.sample(deck, draw_count)

    drawn: List[Dict[str, Any]] = []
    for index, card in enumerate(picked):
        reversed_card = rng.random() < 0.28
        position = positions[index] if index < len(positions) else f"카드 {index + 1}"
        drawn.append(
            {
                "id": card["id"],
                "number": card["number"],
                "name_en": card["name_en"],
                "name_ko": card["name_ko"],
                "symbol": card["symbol"],
                "keywords_ko": card["keywords_ko"],
                "gradient": card["gradient"],
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
    }


def build_local_reading(user_story: str, draw_result: Dict[str, Any]) -> Dict[str, Any]:
    cards = draw_result.get("cards") or []
    card_lines: List[Dict[str, str]] = []
    themes: List[str] = []

    for card in cards:
        orientation = "역방향" if card.get("reversed") else "정방향"
        card_lines.append(
            {
                "position": card.get("position", ""),
                "title": f"{card['name_ko']} ({card['name_en']}) · {orientation}",
                "meaning": card.get("meaning_ko", ""),
                "psychology_theme": card.get("psychology_theme", ""),
            }
        )
        if card.get("psychology_theme"):
            themes.append(card["psychology_theme"])

    primary = cards[0] if cards else {}
    summary_parts = [
        f"질문과 상황을 바탕으로 {len(cards)}장의 카드가 전하는 메시지를 정리했어요.",
    ]
    if user_story.strip():
        summary_parts.append("말씀해 주신 마음을 충분히 담아 해석했습니다.")
    if primary:
        summary_parts.append(
            f"핵심 카드 '{primary.get('name_ko', '')}'는 {primary.get('psychology_theme', '지금의 마음')}과 연결됩니다."
        )

    cbt_actions = [
        "오늘 카드가 비춘 감정을 한 문장으로 적어 보세요.",
        "내일 시도할 아주 작은 행동 하나를 정해 보세요.",
    ]
    if "직장" in user_story or "회사" in user_story:
        cbt_actions[1] = "직장에서 통제 가능한 작은 한 가지를 정해 실천해 보세요."

    return {
        "summary": " ".join(summary_parts),
        "cards": card_lines,
        "psychology_themes": themes,
        "cbt_actions": cbt_actions,
        "primary_card": primary.get("name_en", "The Fool"),
    }


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
