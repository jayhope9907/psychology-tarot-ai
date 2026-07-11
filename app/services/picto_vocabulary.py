"""그림·픽토그램 전용 어휘 (장애인·난독·AAC 친화)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# 기분 프리셋 → 5축 차원
MOOD_PRESETS: Dict[str, Dict[str, int]] = {
    "mood_happy": {"valence": 5, "energy": 4, "anxiety": 2, "social": 4, "sleep": 4},
    "mood_calm": {"valence": 4, "energy": 3, "anxiety": 2, "social": 3, "sleep": 4},
    "mood_ok": {"valence": 3, "energy": 3, "anxiety": 3, "social": 3, "sleep": 3},
    "mood_sad": {"valence": 2, "energy": 2, "anxiety": 3, "social": 2, "sleep": 3},
    "mood_angry": {"valence": 2, "energy": 4, "anxiety": 4, "social": 2, "sleep": 3},
    "mood_scared": {"valence": 2, "energy": 3, "anxiety": 5, "social": 2, "sleep": 2},
    "mood_tired": {"valence": 3, "energy": 1, "anxiety": 2, "social": 3, "sleep": 1},
    "mood_confused": {"valence": 3, "energy": 2, "anxiety": 4, "social": 2, "sleep": 3},
}

PICTO_ITEMS: Dict[str, Dict[str, Any]] = {
    # ── 홈 ──
    "nav_mood": {"emoji": "💚", "phrase": "지금 기분", "category": "nav"},
    "nav_talk": {"emoji": "💬", "phrase": "그림으로 말하기", "category": "nav"},
    "nav_cards": {"emoji": "🃏", "phrase": "카드 그림", "category": "nav"},
    "nav_help": {"emoji": "🆘", "phrase": "도움·전화", "category": "nav"},
    "nav_history": {"emoji": "📅", "phrase": "기분 기록", "category": "nav"},
    # ── 기분 ──
    "mood_happy": {"emoji": "😊", "phrase": "기쁨·좋아요", "category": "mood", "color": "#FFE566"},
    "mood_calm": {"emoji": "😌", "phrase": "편안해요", "category": "mood", "color": "#A8E6CF"},
    "mood_ok": {"emoji": "😐", "phrase": "그냥 그래요", "category": "mood", "color": "#E0E0E0"},
    "mood_sad": {"emoji": "😢", "phrase": "슬퍼요", "category": "mood", "color": "#9EC5E8"},
    "mood_angry": {"emoji": "😠", "phrase": "화나요", "category": "mood", "color": "#FF8A80"},
    "mood_scared": {"emoji": "😰", "phrase": "무서워요·불안", "category": "mood", "color": "#CE93D8"},
    "mood_tired": {"emoji": "😴", "phrase": "피곤해요", "category": "mood", "color": "#B0BEC5"},
    "mood_confused": {"emoji": "😵‍💫", "phrase": "헷갈려요", "category": "mood", "color": "#D1C4E9"},
    # ── 말하기 ──
    "talk_want_chat": {"emoji": "💬", "phrase": "이야기하고 싶어요", "category": "talk"},
    "talk_want_hug": {"emoji": "🤗", "phrase": "안아주세요", "category": "talk"},
    "talk_want_quiet": {"emoji": "🤫", "phrase": "조용히 쉬고 싶어요", "category": "talk"},
    "talk_want_walk": {"emoji": "🚶", "phrase": "나가고 싶어요", "category": "talk"},
    "talk_want_home": {"emoji": "🏠", "phrase": "집에 가고 싶어요", "category": "talk"},
    "talk_hurt": {"emoji": "🤕", "phrase": "아파요", "category": "talk"},
    "talk_hungry": {"emoji": "🍎", "phrase": "배고파요", "category": "talk"},
    "talk_thirsty": {"emoji": "💧", "phrase": "물 마시고 싶어요", "category": "talk"},
    "talk_alone": {"emoji": "🧍", "phrase": "혼자 있고 싶어요", "category": "talk"},
    "talk_together": {"emoji": "👥", "phrase": "같이 있고 싶어요", "category": "talk"},
    "talk_yes": {"emoji": "👍", "phrase": "네·좋아요", "category": "talk"},
    "talk_no": {"emoji": "👎", "phrase": "아니요·싫어요", "category": "talk"},
    "talk_stop": {"emoji": "✋", "phrase": "그만·멈춰", "category": "talk"},
    "talk_wait": {"emoji": "⏳", "phrase": "기다려 주세요", "category": "talk"},
    "talk_thanks": {"emoji": "🙏", "phrase": "고마워요", "category": "talk"},
    "talk_help_me": {"emoji": "🆘", "phrase": "도와주세요", "category": "talk"},
    "talk_scared": {"emoji": "😨", "phrase": "무서워요", "category": "talk"},
    "talk_bored": {"emoji": "😑", "phrase": "심심해요", "category": "talk"},
    "talk_rest": {"emoji": "🛏️", "phrase": "자고 싶어요", "category": "talk"},
    "talk_love": {"emoji": "💕", "phrase": "사랑해요·좋아해요", "category": "talk"},
    # ── 카드 상징 ──
    "card_sun": {"emoji": "☀️", "phrase": "밝음·희망", "category": "card", "tarot": "The Sun"},
    "card_moon": {"emoji": "🌙", "phrase": "조용·꿈", "category": "card", "tarot": "The Moon"},
    "card_star": {"emoji": "⭐", "phrase": "희망·치유", "category": "card", "tarot": "The Star"},
    "card_heart": {"emoji": "❤️", "phrase": "사랑·마음", "category": "card", "tarot": "The Lovers"},
    "card_tree": {"emoji": "🌳", "phrase": "성장·힘", "category": "card", "tarot": "Strength"},
    "card_path": {"emoji": "🛤️", "phrase": "새 길", "category": "card", "tarot": "The Fool"},
    # ── 도움 ──
    "help_1393": {"emoji": "📞", "phrase": "1393 자살예방", "category": "help", "tel": "1393"},
    "help_119": {"emoji": "🚑", "phrase": "119 응급", "category": "help", "tel": "119"},
    "help_129": {"emoji": "💚", "phrase": "129 마음 crisis", "category": "help", "tel": "129"},
    "help_caregiver": {"emoji": "👨‍👩‍👧", "phrase": "보호자·돌봄이", "category": "help"},
}

REPLY_PICTO_KEYWORDS: Dict[str, List[str]] = {
    "talk_yes": ("네", "좋", "그래", "응", "맞"),
    "talk_thanks": ("고마", "감사"),
    "talk_want_quiet": ("쉬", "천천", "편하", "조용"),
    "talk_want_hug": ("안아", "곁", "함께", "들"),
    "mood_calm": ("괜찮", "평온", "안정"),
    "mood_happy": ("기쁨", "밝", "좋"),
    "talk_wait": ("잠깐", "기다", "시간"),
    "talk_help_me": ("도움", "전문", "1393", "119"),
}

OFFLINE_CHAT_TEMPLATES: Dict[str, str] = {
    "talk_help_me": "도움이 필요해 보여요. 보호자를 불러주거나 📞 1393·119·129로 연결해 주세요.",
    "talk_hurt": "아프군요. 천천히 쉬어도 괜찮아요. 필요하면 도움을 요청해 주세요.",
    "talk_scared": "무서울 수 있어요. 지금은 안전한 곳에 있어요. 천천히 숨 쉬어 봐요.",
    "talk_want_hug": "곁에 있어 줄게요. 괜찮아요.",
    "talk_want_quiet": "조용히 쉬어도 좋아요. 편할 때까지 기다릴게요.",
    "talk_hungry": "배고프군요. 먹을 것이 필요해요.",
    "talk_thirsty": "물을 마셔도 좋아요.",
    "talk_rest": "피곤하면 잠깐 쉬거나 자도 괜찮아요.",
    "talk_no": "알겠어요. 원하지 않는 것은 멈출게요.",
    "talk_stop": "멈출게요. 괜찮아요.",
    "talk_love": "마음 전해 줘서 고마워요.",
    "talk_thanks": "천만에요. 함께 있어요.",
    "default": "말해 줘서 고마워요. 함께 있어요. 천천히 괜찮아질 거예요.",
}


def picto_catalog() -> Dict[str, Any]:
    categories = [
        {"id": "nav", "emoji": "🏠", "title": "메뉴"},
        {"id": "mood", "emoji": "💚", "title": "기분"},
        {"id": "talk", "emoji": "💬", "title": "말하기"},
        {"id": "card", "emoji": "🃏", "title": "카드"},
        {"id": "help", "emoji": "🆘", "title": "도움"},
    ]
    items = [
        {"id": pid, **{k: v for k, v in meta.items() if k != "tarot"}}
        for pid, meta in PICTO_ITEMS.items()
    ]
    return {
        "mode": "picture_only",
        "description": "그림·이모지만으로 마음을 표현하는 쉬운 모드입니다.",
        "accessibility_note": "보호자는 우측 상단 👁️으로 글자 라벨을 켤 수 있습니다.",
        "categories": categories,
        "items": items,
        "mood_presets": list(MOOD_PRESETS.keys()),
        "home_nav": ["nav_mood", "nav_talk", "nav_cards", "nav_help", "nav_history"],
        "mood_ids": [k for k in MOOD_PRESETS],
        "talk_ids": [k for k, v in PICTO_ITEMS.items() if v["category"] == "talk"],
        "card_ids": [k for k, v in PICTO_ITEMS.items() if v["category"] == "card"],
        "help_ids": [k for k, v in PICTO_ITEMS.items() if v["category"] == "help"],
    }


def picto_item(picto_id: str) -> Optional[Dict[str, Any]]:
    meta = PICTO_ITEMS.get(picto_id)
    if not meta:
        return None
    return {"id": picto_id, **meta}


def compose_picto_message(picto_ids: List[str]) -> str:
    parts: List[str] = []
    for pid in picto_ids:
        item = PICTO_ITEMS.get(pid)
        if item:
            parts.append(f"{item['emoji']}{item['phrase']}")
    if not parts:
        return ""
    return "[그림 대화] " + " · ".join(parts)


def mood_dimensions_from_picto(mood_id: str) -> Optional[Dict[str, int]]:
    return MOOD_PRESETS.get(mood_id)


CARD_REPLY_TEXT: Dict[str, str] = {
    "card_sun": "오늘은 밝은 기운이 가까이 있어요. 천천히 숨 쉬어 보세요.",
    "card_moon": "조용한 밤처럼 쉬어도 괜찮아요. 꿈과 마음을 천천히 들여다봐요.",
    "card_star": "희망의 별이 보여요. 작은 한 걸음도 소중해요.",
    "card_heart": "마음이 중요해요. 사랑과 연결을 느껴보세요.",
    "card_tree": "천천히 자라는 힘을 믿어요. 당신 안에 힘이 있어요.",
    "card_path": "새 길이 열려 있어요. 두려워도 괜찮아요.",
}


def picto_card_reply(card_id: str) -> Dict[str, Any]:
    item = picto_item(card_id)
    if not item:
        return {"reply_text": "오늘도 함께해요.", "reply_pictos": suggest_reply_pictos("괜찮", 4)}
    text = CARD_REPLY_TEXT.get(card_id, f"{item['phrase']}의 기운을 느껴보세요.")
    return {"reply_text": text, "reply_pictos": suggest_reply_pictos(text, 4)}


def suggest_reply_pictos(assistant_text: str, limit: int = 4) -> List[Dict[str, Any]]:
    blob = (assistant_text or "").lower()
    ranked: List[str] = []
    for picto_id, keywords in REPLY_PICTO_KEYWORDS.items():
        if any(kw in blob for kw in keywords):
            ranked.append(picto_id)
    if not ranked:
        ranked = ["talk_yes", "mood_calm", "talk_thanks", "talk_want_quiet"]
    out: List[Dict[str, Any]] = []
    for pid in ranked[:limit]:
        item = picto_item(pid)
        if item:
            out.append(item)
    return out


def picto_offline_bundle() -> Dict[str, Any]:
    """전체 그림 사전 + 오프라인 대화·카드·기분 데이터."""
    bundle = picto_catalog()
    bundle["bundle_version"] = 1
    bundle["card_replies"] = dict(CARD_REPLY_TEXT)
    bundle["mood_dimensions"] = {k: dict(v) for k, v in MOOD_PRESETS.items()}
    bundle["reply_keywords"] = {k: list(v) for k, v in REPLY_PICTO_KEYWORDS.items()}
    bundle["offline_chat_templates"] = dict(OFFLINE_CHAT_TEMPLATES)
    return bundle


def offline_chat_reply(picto_ids: List[str]) -> Dict[str, Any]:
    for pid in picto_ids:
        if pid in OFFLINE_CHAT_TEMPLATES and pid != "default":
            text = OFFLINE_CHAT_TEMPLATES[pid]
            return {"reply_text": text, "reply_pictos": suggest_reply_pictos(text, 4), "offline": True}
    text = OFFLINE_CHAT_TEMPLATES["default"]
    return {"reply_text": text, "reply_pictos": suggest_reply_pictos(text, 4), "offline": True}


def _score_dimensions_match(preset: Dict[str, int], dims: Dict[str, int]) -> int:
    return sum(abs(preset.get(k, 3) - dims.get(k, 3)) for k in ("valence", "energy", "anxiety", "social", "sleep"))


def infer_mood_picto_from_checkin(checkin: Dict[str, Any]) -> Dict[str, Any]:
    note = (checkin.get("note") or "").strip()
    for mood_id in MOOD_PRESETS:
        item = picto_item(mood_id)
        if not item:
            continue
        phrase = item.get("phrase", "")
        emoji = item.get("emoji", "")
        if emoji and emoji in note:
            return {"mood_picto_id": mood_id, "emoji": emoji, "phrase": phrase}
        if phrase and phrase in note:
            return {"mood_picto_id": mood_id, "emoji": emoji, "phrase": phrase}

    dims = checkin.get("dimensions") or {}
    if dims:
        best_id = min(MOOD_PRESETS, key=lambda mid: _score_dimensions_match(MOOD_PRESETS[mid], dims))
        item = picto_item(best_id) or {}
        return {"mood_picto_id": best_id, "emoji": item.get("emoji", "💚"), "phrase": item.get("phrase", "")}

    score = int(checkin.get("mood_score") or 3)
    fallback = {
        5: "mood_happy",
        4: "mood_calm",
        3: "mood_ok",
        2: "mood_sad",
        1: "mood_sad",
    }.get(score, "mood_ok")
    item = picto_item(fallback) or {}
    return {"mood_picto_id": fallback, "emoji": item.get("emoji", "💚"), "phrase": item.get("phrase", "")}


def build_picto_mood_timeline(checkins: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    timeline: List[Dict[str, Any]] = []
    for row in checkins:
        picto = infer_mood_picto_from_checkin(row)
        timeline.append(
            {
                "date": row.get("checkin_date") or row.get("date"),
                "emoji": picto["emoji"],
                "mood_picto_id": picto["mood_picto_id"],
                "mood_score": row.get("mood_score"),
            }
        )
    return timeline
