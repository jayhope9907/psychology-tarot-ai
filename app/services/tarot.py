from __future__ import annotations

import hashlib
import json
import os
import random
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.services.tarot_rules import (
    DEFAULT_SPREAD,
    REVERSE_CHANCE,
    THREE_CARD_COUNT,
    THREE_CARD_POSITIONS,
    enrich_card_rules,
    narrative_rules_block,
    position_summary_lines,
    rules_manifest,
)

_DECK_PATH = Path(__file__).resolve().parent.parent / "data" / "tarot_deck.json"
_MINOR_PATH = Path(__file__).resolve().parent.parent / "data" / "minor_arcana.json"
_DECK_CACHE: Optional[Dict[str, Any]] = None
_MINOR_CACHE: Optional[List[Dict[str, Any]]] = None
_FULL_DECK_CACHE: Optional[List[Dict[str, Any]]] = None

THREE_CARD_POSITION_GUIDE = tuple(
    (pos["label_ko"], pos["guide_ko"]) for pos in THREE_CARD_POSITIONS
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


_WIKIMEDIA_UA = "MaumShelterAI/1.0 (educational-wellness; contact=license@maum-shelter.example)"


def _image_cache_dir() -> Path:
    override = (os.getenv("TAROT_IMAGE_CACHE_DIR") or "").strip()
    if override:
        return Path(override)
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
        return Path(tempfile.gettempdir()) / "tarot_images"
    return Path(__file__).resolve().parents[2] / ".cache" / "tarot_images"


def remote_card_image_url(card_id: str, image_file: Optional[str] = None) -> str:
    """Public-domain Rider–Waite (and minor) art on Wikimedia Commons."""
    path = _TAROT_IMAGE_PATHS.get(card_id)
    if path:
        filename = path.rsplit("/", 1)[-1]
        # ~500px thumbs keep card textures light while staying original RWS art.
        return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{path}/500px-{filename}"
    if image_file:
        digest = hashlib.md5(image_file.encode()).hexdigest()
        return f"https://upload.wikimedia.org/wikipedia/commons/{digest[0]}/{digest[:2]}/{image_file}"
    return ""


def card_image_url(card_id: str, image_file: Optional[str] = None) -> str:
    """Same-origin URL so Three.js / canvas can use the art without CORS taint."""
    if not remote_card_image_url(card_id, image_file):
        return ""
    return f"/api/v1/tarot/card-image/{card_id}"


def _image_cache_meta(card_id: str, image_file: Optional[str] = None) -> tuple[Path, str]:
    remote = remote_card_image_url(card_id, image_file)
    suffix = ".svg" if remote.lower().endswith(".svg") else ".jpg"
    # Versioned filename so we can bump remote art size without stale full-res caches.
    return _image_cache_dir() / f"{card_id}_v2{suffix}", remote


def _media_type_for_path(path: Path) -> str:
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".gif": "image/gif",
    }.get(path.suffix.lower(), "application/octet-stream")


def _download_remote_image(remote: str) -> Optional[bytes]:
    headers = {"User-Agent": _WIKIMEDIA_UA}
    try:
        import httpx

        with httpx.Client(timeout=20.0, headers=headers, follow_redirects=True) as client:
            response = client.get(remote)
            response.raise_for_status()
            if response.content:
                return response.content
    except Exception:
        pass
    try:
        request = urllib.request.Request(remote, headers=headers)
        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read()
            return data if data else None
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None


def _write_image_cache(cache_path: Path, data: bytes) -> None:
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(data)
    except OSError:
        pass


def fetch_card_image_content(card_id: str) -> Optional[Tuple[bytes, str]]:
    """Return card art bytes + media type (cache-first, then Wikimedia proxy)."""
    card = get_card_by_id(card_id)
    if not card:
        return None
    cache_path, remote = _image_cache_meta(card_id, card.get("image_file"))
    if not remote:
        return None
    media_type = _media_type_for_path(cache_path)
    if cache_path.is_file() and cache_path.stat().st_size > 0:
        return cache_path.read_bytes(), media_type
    data = _download_remote_image(remote)
    if not data:
        return None
    _write_image_cache(cache_path, data)
    return data, media_type


def resolve_card_image_file(card_id: str) -> Optional[Path]:
    """Return a local cached original image path, downloading once if needed."""
    payload = fetch_card_image_content(card_id)
    if not payload:
        return None
    card = get_card_by_id(card_id)
    if not card:
        return None
    cache_path, _remote = _image_cache_meta(card_id, card.get("image_file"))
    return cache_path if cache_path.is_file() and cache_path.stat().st_size > 0 else None


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


def tarot_ui_flags() -> Dict[str, bool]:
    """Hover spoilers stay on for tunnel/local tests; off on Render production."""
    override = os.getenv("TAROT_SHOW_HOVER_HINTS")
    if override is not None and str(override).strip() != "":
        show = str(override).strip().lower() in {"1", "true", "yes", "on"}
    else:
        # Render.com sets RENDER=true on every service.
        show = os.getenv("RENDER", "").lower() not in {"true", "1"}
    return {"show_hover_hints": show}


def _catalog_entry(card: Dict[str, Any], *, redact_meanings: bool = False) -> Dict[str, Any]:
    image_file = card.get("image_file")
    entry = {
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
    if redact_meanings:
        # Keep ids for picking; meanings arrive after draw/pick so hovering cannot spoil.
        entry["name_en"] = ""
        entry["name_ko"] = ""
        entry["keywords_ko"] = []
        entry["upright_ko"] = ""
        entry["reversed_ko"] = ""
        entry["psychology_theme"] = ""
    return entry


def list_deck_catalog() -> Dict[str, Any]:
    ui = tarot_ui_flags()
    redact = not ui["show_hover_hints"]
    cards = [_catalog_entry(card, redact_meanings=redact) for card in get_full_deck()]
    return {
        "cards": cards,
        "spreads": _load_deck()["spreads"],
        "total": len(cards),
        "major_count": len(get_major_arcana()),
        "minor_count": len(get_minor_arcana()),
        "ui": ui,
    }


def normalize_three_card_spread(spread: Optional[str] = None, count: Optional[int] = None) -> tuple[str, int]:
    """Consumer tarot is locked to the classic 3-card spread."""
    return DEFAULT_SPREAD, THREE_CARD_COUNT


def _is_reversed(rng: random.Random | None = None) -> bool:
    if rng is None:
        return random.random() < REVERSE_CHANCE
    return rng.random() < REVERSE_CHANCE


def _finalize_draw(spread: str, spread_meta: Dict[str, Any], drawn: List[Dict[str, Any]]) -> Dict[str, Any]:
    cards = [enrich_card_rules(card) for card in drawn]
    manifest = rules_manifest()
    return {
        "spread": spread,
        "spread_label_ko": spread_meta["label_ko"],
        "positions": [c.get("position") for c in cards],
        "cards": cards,
        "rules": manifest,
        "rules_summary_ko": position_summary_lines(cards),
    }


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

    return _finalize_draw(spread, spread_meta, drawn)


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

    return _finalize_draw(spread, spread_meta, drawn)


def build_local_reading(user_story: str, draw_result: Dict[str, Any]) -> Dict[str, Any]:
    cards = [enrich_card_rules(card) for card in (draw_result.get("cards") or [])]
    card_lines: List[Dict[str, str]] = []
    themes: List[str] = []

    for card in cards:
        orientation = "역방향" if card.get("reversed") else "정방향"
        suit_rule = card.get("suit_rule") or {}
        rank_rule = card.get("rank_rule") or {}
        card_lines.append(
            {
                "position": card.get("position", ""),
                "position_guide": card.get("position_guide", ""),
                "title": f"{card['name_ko']} ({card['name_en']}) · {orientation}",
                "meaning": card.get("meaning_ko", ""),
                "psychology_theme": card.get("psychology_theme", ""),
                "archetype": card.get("archetype", ""),
                "arcana": card.get("arcana", ""),
                "suit_label": suit_rule.get("label_ko", ""),
                "element": suit_rule.get("element_ko", ""),
                "rank_guide": rank_rule.get("guide_ko", ""),
                "orientation_guide": (card.get("orientation_rule") or {}).get("guide_ko", ""),
            }
        )
        if card.get("psychology_theme"):
            themes.append(card["psychology_theme"])

    summary_parts = [
        "클래식 3카드(과거·현재·미래) · 78장 · 정/역 공정 · 위치·수트·아르카나 규칙으로 읽어요.",
    ]
    if user_story.strip():
        summary_parts.append("적어 주신 상황을 바탕으로, 부담 없이 읽을 수 있게 정리했어요.")
    summary_parts.extend(position_summary_lines(cards))

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
        "spread_rules_ko": [f"{p['label_ko']}: {p['guide_ko']}" for p in THREE_CARD_POSITIONS],
        "practice_rules_ko": rules_manifest()["practice_ko"],
    }


def format_draw_for_prompt(draw_result: Dict[str, Any]) -> str:
    lines: List[str] = [
        narrative_rules_block(),
        "",
        "스프레드: 3카드 (과거·뿌리 → 현재·핵심 → 미래·방향)",
    ]
    for card in draw_result.get("cards") or []:
        enriched = enrich_card_rules(card)
        orientation = "역방향" if enriched.get("reversed") else "정방향"
        suit_rule = enriched.get("suit_rule") or {}
        rank_rule = enriched.get("rank_rule") or {}
        arcana = "메이저" if enriched.get("arcana") == "major" else (
            f"마이너 · {suit_rule.get('label_ko', '')}/{suit_rule.get('element_ko', '')}"
            f" · {rank_rule.get('label_ko', '')}"
        )
        lines.append(
            f"- [{enriched.get('position')}] ({enriched.get('position_guide', '')}) · "
            f"{enriched.get('name_ko')} / {orientation} / {arcana} — "
            f"{enriched.get('meaning_ko', '')} · 테마: {enriched.get('psychology_theme', '')} · "
            f"원형: {enriched.get('archetype', '')}"
        )
    return "\n".join(lines)


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
