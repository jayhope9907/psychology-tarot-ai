"""그림·픽토그램 전용 어휘 (AAC·감정인식·표현치료 친화)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

THERAPY_CONCEPT: Dict[str, Any] = {
    "title": "그림마음",
    "subtitle": "말 대신 입체 장면으로 마음을 전하는 표현 모드",
    "therapy_name": "그림 의사소통 · 감정 인식 (AAC / Pictorial Emotion Expression)",
    "therapy_schools": ["표현예술치료", "감정인식 훈련", "게슈탈트 알아차림", "트라우마 정보 안정화"],
    "scholars": ["Margaret Naumburg", "Edith Kramer", "Cathy Malchiodi", "AAC 의사소통 접근"],
    "what_it_is": (
        "그림마음은 글·말이 어렵거나 부담될 때, 입체 장면 카드를 골라 "
        "기분·욕구·도움을 전하는 방식입니다. 정식 진단을 하지 않으며, "
        "자기표현·감정 알아차림·안전한 연결을 돕습니다."
    ),
    "how_to": [
        "장면을 보고 라벨(무슨 마음인지)을 확인해요",
        "지금 기분 또는 하고 싶은 말을 골라요",
        "선택하면 AI·보호자와 연결되거나 기록이 남아요",
        "힘들면 언제든 「도움·전화」로 1393·119·129에 연결할 수 있어요",
    ],
    "safety": "위급하면 1393 · 119 · 129. 그림 선택은 의료 진단이 아닙니다.",
}


def _item(
    emoji: str,
    phrase: str,
    category: str,
    *,
    label: str,
    meaning: str,
    color: Optional[str] = None,
    tel: Optional[str] = None,
    tarot: Optional[str] = None,
    therapy_tag: str = "감정·표현",
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "emoji": emoji,
        "phrase": phrase,
        "category": category,
        "label_ko": label,
        "meaning_ko": meaning,
        "therapy_tag": therapy_tag,
        "scene": None,
    }
    if color:
        row["color"] = color
    if tel:
        row["tel"] = tel
    if tarot:
        row["tarot"] = tarot
    return row


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
    "nav_mood": _item(
        "💚", "지금 기분", "nav",
        label="지금 기분", meaning="오늘의 감정을 입체 장면으로 고르기", therapy_tag="감정인식",
    ),
    "nav_talk": _item(
        "💬", "그림으로 말하기", "nav",
        label="그림으로 말하기", meaning="하고 싶은 말을 장면으로 조합하기", therapy_tag="AAC 의사소통",
    ),
    "nav_cards": _item(
        "🃏", "상징 카드", "nav",
        label="상징 카드", meaning="희망·치유·길 같은 상징을 고르기", therapy_tag="상징·표현치료",
    ),
    "nav_help": _item(
        "🆘", "도움·전화", "nav",
        label="도움·전화", meaning="위기 때 전화·보호자 연결", therapy_tag="안전·위기",
    ),
    "nav_history": _item(
        "📅", "기분 기록", "nav",
        label="기분 기록", meaning="최근 감정 장면 흐름 보기", therapy_tag="자기모니터링",
    ),
    "mood_happy": _item(
        "😊", "기쁨·좋아요", "mood",
        label="기쁨", meaning="밝고 좋은 기분 · 해가 뜬 장면", color="#FFE566", therapy_tag="감정인식",
    ),
    "mood_calm": _item(
        "😌", "편안해요", "mood",
        label="편안함", meaning="안정·평온 · 잔잔한 호수 장면", color="#A8E6CF", therapy_tag="감정인식",
    ),
    "mood_ok": _item(
        "😐", "그냥 그래요", "mood",
        label="그저 그럼", meaning="특별할 것 없는 보통 기분", color="#E0E0E0", therapy_tag="감정인식",
    ),
    "mood_sad": _item(
        "😢", "슬퍼요", "mood",
        label="슬픔", meaning="가라앉은 마음 · 비 오는 장면", color="#9EC5E8", therapy_tag="감정인식",
    ),
    "mood_angry": _item(
        "😠", "화나요", "mood",
        label="화남", meaning="열이 오른 마음 · 불꽃 장면", color="#FF8A80", therapy_tag="감정인식",
    ),
    "mood_scared": _item(
        "😰", "무서워요·불안", "mood",
        label="불안·두려움", meaning="긴장·무서움 · 번개 장면", color="#CE93D8", therapy_tag="감정인식",
    ),
    "mood_tired": _item(
        "😴", "피곤해요", "mood",
        label="피곤함", meaning="에너지가 바닥난 상태 · 달밤", color="#B0BEC5", therapy_tag="감정인식",
    ),
    "mood_confused": _item(
        "😵‍💫", "헷갈려요", "mood",
        label="혼란", meaning="생각이 엉킨 느낌 · 소용돌이", color="#D1C4E9", therapy_tag="감정인식",
    ),
    "talk_want_chat": _item(
        "💬", "이야기하고 싶어요", "talk",
        label="이야기하고 싶어요", meaning="누군가와 대화가 필요해요", therapy_tag="AAC",
    ),
    "talk_want_hug": _item(
        "🤗", "안아주세요", "talk",
        label="안아주세요", meaning="따뜻함·접촉이 필요해요", therapy_tag="AAC",
    ),
    "talk_want_quiet": _item(
        "🤫", "조용히 쉬고 싶어요", "talk",
        label="조용히 쉴래요", meaning="자극을 줄이고 쉬고 싶어요", therapy_tag="AAC",
    ),
    "talk_want_walk": _item(
        "🚶", "나가고 싶어요", "talk",
        label="나가고 싶어요", meaning="밖으로 움직이고 싶어요", therapy_tag="AAC",
    ),
    "talk_want_home": _item(
        "🏠", "집에 가고 싶어요", "talk",
        label="집에 가고 싶어요", meaning="안전한 집으로 돌아가고 싶어요", therapy_tag="AAC",
    ),
    "talk_hurt": _item(
        "🤕", "아파요", "talk",
        label="아파요", meaning="몸이나 마음이 아파요", therapy_tag="AAC",
    ),
    "talk_hungry": _item(
        "🍎", "배고파요", "talk",
        label="배고파요", meaning="음식이 필요해요", therapy_tag="AAC",
    ),
    "talk_thirsty": _item(
        "💧", "물 마시고 싶어요", "talk",
        label="목말라요", meaning="물이 필요해요", therapy_tag="AAC",
    ),
    "talk_alone": _item(
        "🧍", "혼자 있고 싶어요", "talk",
        label="혼자 있을래요", meaning="잠시 혼자만의 공간이 필요해요", therapy_tag="AAC",
    ),
    "talk_together": _item(
        "👥", "같이 있고 싶어요", "talk",
        label="같이 있고 싶어요", meaning="곁에 누군가 있으면 좋겠어요", therapy_tag="AAC",
    ),
    "talk_yes": _item(
        "👍", "네·좋아요", "talk",
        label="네 / 좋아요", meaning="동의·수락", therapy_tag="AAC",
    ),
    "talk_no": _item(
        "👎", "아니요·싫어요", "talk",
        label="아니요 / 싫어요", meaning="거절·싫음", therapy_tag="AAC",
    ),
    "talk_stop": _item(
        "✋", "그만·멈춰", "talk",
        label="그만 / 멈춰요", meaning="지금 활동을 멈춰 주세요", therapy_tag="AAC",
    ),
    "talk_wait": _item(
        "⏳", "기다려 주세요", "talk",
        label="기다려 주세요", meaning="시간이 더 필요해요", therapy_tag="AAC",
    ),
    "talk_thanks": _item(
        "🙏", "고마워요", "talk",
        label="고마워요", meaning="감사의 마음", therapy_tag="AAC",
    ),
    "talk_help_me": _item(
        "🆘", "도와주세요", "talk",
        label="도와주세요", meaning="도움이 필요해요", therapy_tag="안전",
    ),
    "talk_scared": _item(
        "😨", "무서워요", "talk",
        label="무서워요", meaning="두렵고 불안해요", therapy_tag="AAC",
    ),
    "talk_bored": _item(
        "😑", "심심해요", "talk",
        label="심심해요", meaning="자극·활동이 필요해요", therapy_tag="AAC",
    ),
    "talk_rest": _item(
        "🛏️", "자고 싶어요", "talk",
        label="자고 싶어요", meaning="휴식·수면이 필요해요", therapy_tag="AAC",
    ),
    "talk_love": _item(
        "💕", "사랑해요·좋아해요", "talk",
        label="좋아해요", meaning="애정·호감을 전해요", therapy_tag="AAC",
    ),
    "card_sun": _item(
        "☀️", "밝음·희망", "card",
        label="태양 · 밝음", meaning="희망과 생기 상징", tarot="The Sun", therapy_tag="상징치료",
    ),
    "card_moon": _item(
        "🌙", "조용·꿈", "card",
        label="달 · 고요", meaning="휴식과 내면의 꿈", tarot="The Moon", therapy_tag="상징치료",
    ),
    "card_star": _item(
        "⭐", "희망·치유", "card",
        label="별 · 치유", meaning="회복과 희망의 별", tarot="The Star", therapy_tag="상징치료",
    ),
    "card_heart": _item(
        "❤️", "사랑·마음", "card",
        label="하트 · 마음", meaning="사랑과 연결", tarot="The Lovers", therapy_tag="상징치료",
    ),
    "card_tree": _item(
        "🌳", "성장·힘", "card",
        label="나무 · 성장", meaning="뿌리 내린 힘과 성장", tarot="Strength", therapy_tag="상징치료",
    ),
    "card_path": _item(
        "🛤️", "새 길", "card",
        label="길 · 시작", meaning="새로운 선택의 길", tarot="The Fool", therapy_tag="상징치료",
    ),
    "help_1393": _item(
        "📞", "1393 자살예방", "help",
        label="1393 전화", meaning="자살예방 상담전화", tel="1393", therapy_tag="위기개입",
    ),
    "help_119": _item(
        "🚑", "119 응급", "help",
        label="119 응급", meaning="응급 구조·의료", tel="119", therapy_tag="위기개입",
    ),
    "help_129": _item(
        "💚", "129 마음 crisis", "help",
        label="129 정신건강", meaning="정신건강 위기상담", tel="129", therapy_tag="위기개입",
    ),
    "help_caregiver": _item(
        "👨‍👩‍👧", "보호자·돌봄이", "help",
        label="보호자 알림", meaning="돌보는 사람에게 도움 요청", therapy_tag="위기개입",
    ),
}

for _pid, _meta in PICTO_ITEMS.items():
    _meta["scene"] = _pid

REPLY_PICTO_KEYWORDS: Dict[str, Tuple[str, ...]] = {
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
        "description": THERAPY_CONCEPT["subtitle"],
        "therapy_concept": THERAPY_CONCEPT,
        "accessibility_note": "모든 장면 아래에 이름과 뜻이 표시됩니다. 소리 듣기로 읽어 줄 수 있습니다.",
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
    bundle["bundle_version"] = 2
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
