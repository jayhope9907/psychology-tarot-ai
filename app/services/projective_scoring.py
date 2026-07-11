"""투영검사 질적·테마 채점 — 임상심리 참고 (진단 아님)."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from app.services.dsm5_framework import score_text_against_spectra

THEME_KEYWORDS: Dict[str, List[str]] = {
    "anxiety": ["불안", "걱정", "두려", "무서", "초조", "긴장", "panic", "anxiety"],
    "depression": ["우울", "슬픔", "무기력", "허무", "절망", "공허", "depress", "sad"],
    "hostility": ["화", "분노", "공격", "미워", "원한", "적", "hostil", "anger"],
    "dependency": ["의존", "도움", "혼자", "외로", "버림", "attach", "lonely", "alone"],
    "hope": ["희망", "기대", "성장", "나아", "회복", "밝", "hope", "future"],
    "isolation": ["고립", "단절", "외톨", "담", "벽", "멀", "isolate", "withdraw"],
    "conflict": ["갈등", "싸움", "대립", "충돌", "conflict", "fight"],
    "security": ["안전", "편안", "따뜻", "보호", "안정", "safe", "secure"],
}

HTP_SIZE_HINTS = {
    "large": "확장·표출·에너지 과잉 가능성 (질적)",
    "small": "위축·불안·자기 축소 가능성 (질적)",
    "balanced": "균형적 표현",
}

INKBLOT_CONTENT_HINTS = {
    "human": ["사람", "인간", "남자", "여자", "아이", "얼굴", "figure", "person"],
    "animal": ["동물", "새", "나비", "곤충", "animal", "bird", "butterfly"],
    "nature": ["나무", "꽃", "구름", "산", "물", "tree", "cloud", "flower"],
    "abstract": ["추상", "무늬", "패턴", "색", "abstract", "pattern"],
}


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        parts = [str(v) for v in value.values() if v]
        return " ".join(parts)
    return str(value).strip()


def score_text_themes(text: str) -> Dict[str, float]:
    blob = (text or "").lower()
    if not blob:
        return {}
    scores: Dict[str, float] = {}
    for theme, keywords in THEME_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in blob)
        if hits:
            scores[theme] = round(min(1.0, hits * 0.25), 2)
    return scores


def score_drawing_meta(meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    meta = meta or {}
    stroke_count = int(meta.get("stroke_count") or 0)
    canvas_w = float(meta.get("canvas_width") or 400)
    canvas_h = float(meta.get("canvas_height") or 400)
    bbox_w = float(meta.get("bbox_width") or 0)
    bbox_h = float(meta.get("bbox_height") or 0)
    fill_ratio = round((bbox_w * bbox_h) / max(1, canvas_w * canvas_h), 3) if bbox_w and bbox_h else 0.0

    size_hint = "balanced"
    if fill_ratio >= 0.35:
        size_hint = "large"
    elif fill_ratio > 0 and fill_ratio < 0.08:
        size_hint = "small"

    line_pressure = "moderate"
    if stroke_count > 120:
        line_pressure = "heavy"
    elif stroke_count > 0 and stroke_count < 15:
        line_pressure = "light"

    return {
        "stroke_count": stroke_count,
        "fill_ratio": fill_ratio,
        "size_hint": HTP_SIZE_HINTS.get(size_hint, size_hint),
        "line_pressure": line_pressure,
        "has_drawing": bool(meta.get("has_strokes") or stroke_count > 0),
    }


def score_inkblot_association(text: str) -> Dict[str, Any]:
    blob = text.lower()
    categories = [cat for cat, kws in INKBLOT_CONTENT_HINTS.items() if any(k in blob for k in kws)]
    themes = score_text_themes(text)
    return {
        "content_categories": categories or ["unclassified"],
        "themes": themes,
        "response_length": len(text),
        "multiple_percepts": len(re.split(r"[,·/]|그리고|또", text)) if text else 0,
    }


def score_tat_story(story: Dict[str, Any]) -> Dict[str, Any]:
    merged = " ".join(_normalize_text(story.get(k)) for k in ("happening", "feeling", "outcome"))
    themes = score_text_themes(merged)
    hero = story.get("hero") or story.get("happening", "")[:40]
    need_press = []
    if themes.get("conflict"):
        need_press.append("conflict_press")
    if themes.get("dependency"):
        need_press.append("affiliation_need")
    if themes.get("hope"):
        need_press.append("achievement_need")
    return {
        "themes": themes,
        "need_press_hints": need_press or ["exploratory"],
        "hero_focus": hero[:80] if hero else "",
        "outcome_tone": "positive" if themes.get("hope", 0) > themes.get("depression", 0) else "mixed",
        "spectrum_signals": score_text_against_spectra(merged) if merged else {},
    }


def score_item_response(item_id: str, response_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if response_type == "drawing":
        association = _normalize_text(payload.get("association"))
        drawing_meta = score_drawing_meta(payload.get("meta"))
        text_themes = score_text_themes(association)
        return {
            "type": "drawing",
            "drawing_meta": drawing_meta,
            "association_themes": text_themes,
            "qualitative_tags": _drawing_tags(item_id, drawing_meta, text_themes),
        }
    if response_type == "inkblot":
        text = _normalize_text(payload.get("association") or payload.get("text"))
        ink = score_inkblot_association(text)
        ink["themes"] = {**ink.get("themes", {}), **score_text_themes(text)}
        return {"type": "inkblot", **ink}
    if response_type == "tat_story":
        story = payload.get("story") or payload
        return {"type": "tat_story", **score_tat_story(story if isinstance(story, dict) else {"happening": story})}
    text = _normalize_text(payload.get("text"))
    return {
        "type": "open_text",
        "themes": score_text_themes(text),
        "spectrum_signals": score_text_against_spectra(text) if text else {},
        "excerpt": text[:200],
    }


def _drawing_tags(item_id: str, meta: Dict[str, Any], themes: Dict[str, float]) -> List[str]:
    tags: List[str] = []
    prefix = item_id.split("_")[0]
    if prefix == "htp":
        tags.append(f"htp_{item_id.replace('htp_', '')}")
    elif prefix == "dap":
        tags.append("dap_person")
    elif prefix == "kfd":
        tags.append("kfd_family")
    if meta.get("size_hint"):
        tags.append(f"size_{meta['size_hint'].split('·')[0][:6]}")
    top_theme = max(themes, key=themes.get) if themes else None
    if top_theme:
        tags.append(f"theme_{top_theme}")
    return tags


def score_projective_battery(answers: Dict[str, Dict[str, Any]], catalog_items: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    instrument_scores: Dict[str, Any] = {}
    all_themes: Dict[str, float] = {}

    for instrument_id, item_answers in answers.items():
        item_scores: Dict[str, Any] = {}
        for item_id, payload in item_answers.items():
            meta = catalog_items.get(item_id, {})
            rt = meta.get("response_type", payload.get("response_type", "open_text"))
            scored = score_item_response(item_id, rt, payload)
            item_scores[item_id] = scored
            for theme, val in (scored.get("themes") or scored.get("association_themes") or {}).items():
                all_themes[theme] = round(max(all_themes.get(theme, 0), val), 2)

        instrument_scores[instrument_id] = {
            "completed_items": len(item_answers),
            "item_scores": item_scores,
            "dominant_themes": _top_themes(item_scores, 3),
        }

    return {
        "instruments": instrument_scores,
        "global_themes": dict(sorted(all_themes.items(), key=lambda x: -x[1])[:6]),
        "interpretation_note": (
            "투사검사 해석은 반응의 질적 패턴·테마를 참고한 탐색용 요약입니다. "
            "임상 진단은 면접·병력·표준화 도구와 함께 전문가가 수행합니다."
        ),
    }


def _top_themes(item_scores: Dict[str, Any], n: int) -> List[str]:
    pool: Dict[str, float] = {}
    for scored in item_scores.values():
        for theme, val in (scored.get("themes") or scored.get("association_themes") or {}).items():
            pool[theme] = max(pool.get(theme, 0), val)
    return [t for t, _ in sorted(pool.items(), key=lambda x: -x[1])[:n]]
