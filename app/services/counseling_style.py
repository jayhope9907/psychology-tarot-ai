from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

DEFAULT_TONE = {"warmth": 4, "formality": 2, "pace": 3, "directness": 2}

TEXTURE_PRESETS: Dict[str, Dict[str, str]] = {
    "calm": {
        "label": "고요한",
        "description": "차분하고 안정적인 말투. 호흡을 길게 가져갑니다.",
        "prompt": "차분하고 여유 있는 호흡. 문장을 짧게 끊고, 침묵도 허용하세요.",
    },
    "warm": {
        "label": "포근한",
        "description": "따뜻하고 포근한 질감. 위로와 수용이 중심입니다.",
        "prompt": "포근하고 따뜻한 말투. '~해도 괜찮아요'처럼 수용적 표현을 사용하세요.",
    },
    "professional": {
        "label": "전문적",
        "description": "명확하고 구조적인 상담 톤.",
        "prompt": "전문적이되 차갑지 않게. 구조는 유지하되 판단하지 마세요.",
    },
    "intimate": {
        "label": "친밀한",
        "description": "가까운 거리감, 속 이야기를 꺼내기 쉬운 톤.",
        "prompt": "친밀하지만 경계를 지키세요. '함께'라는 느낌을 주되 과하지 않게.",
    },
    "energetic": {
        "label": "활기찬",
        "description": "밝고 힘을 실어 주는 톤.",
        "prompt": "밝고 지지적이지만 가볍게 넘기지 마세요. 진심 어린 활력을 전달하세요.",
    },
}

COUNSELORS: Dict[str, Dict[str, Any]] = {
    "seoyeon": {
        "id": "seoyeon",
        "name": "이서연",
        "gender": "female",
        "title": "AI 웰니스 가이드",
        "tagline": "따뜻한 공감 · 수용 중심",
        "default_voice": "female_seoyeon_soft",
        "default_texture": "warm",
    },
    "jieun": {
        "id": "jieun",
        "name": "박지은",
        "gender": "female",
        "title": "AI 마음 가이드",
        "tagline": "부드럽고 차분한 위로",
        "default_voice": "female_jieun_gentle",
        "default_texture": "calm",
    },
    "yuna": {
        "id": "yuna",
        "name": "최유나",
        "gender": "female",
        "title": "AI 마음 가이드",
        "tagline": "밝고 지지적인 대화",
        "default_voice": "female_yuna_bright",
        "default_texture": "energetic",
    },
    "soyul": {
        "id": "soyul",
        "name": "한소율",
        "gender": "female",
        "title": "AI 웰니스 가이드",
        "tagline": "친밀하고 섬세한 경청",
        "default_voice": "female_soyul_intimate",
        "default_texture": "intimate",
    },
    "minjun": {
        "id": "minjun",
        "name": "김민준",
        "gender": "male",
        "title": "AI 웰니스 가이드",
        "tagline": "든든하고 안정적인 동행",
        "default_voice": "male_minjun_warm",
        "default_texture": "warm",
    },
    "junho": {
        "id": "junho",
        "name": "이준호",
        "gender": "male",
        "title": "AI 마음 가이드",
        "tagline": "깊고 차분한 통찰",
        "default_voice": "male_junho_deep",
        "default_texture": "calm",
    },
    "seojun": {
        "id": "seojun",
        "name": "박서준",
        "gender": "male",
        "title": "AI 마음 가이드",
        "tagline": "명확하고 전문적인 안내",
        "default_voice": "male_seojun_clear",
        "default_texture": "professional",
    },
    "woojin": {
        "id": "woojin",
        "name": "정우진",
        "gender": "male",
        "title": "AI 웰니스 가이드",
        "tagline": "편안하고 친근한 대화",
        "default_voice": "male_woojin_friendly",
        "default_texture": "intimate",
    },
}

VOICE_PRESETS: Dict[str, Dict[str, Any]] = {
    "female_seoyeon_soft": {
        "id": "female_seoyeon_soft",
        "label": "이서연 · 부드러운",
        "gender": "female",
        "counselor_id": "seoyeon",
        "pitch": 1.06,
        "rate": 0.9,
        "volume": 1.0,
        "tags": ["부드러움", "따뜻", "여성", "저속"],
        "voice_hints": ["SunHi", "Heami", "Yuna", "Female", "여성", "Google 한국의"],
    },
    "female_seoyeon_clear": {
        "id": "female_seoyeon_clear",
        "label": "이서연 · 또렷한",
        "gender": "female",
        "counselor_id": "seoyeon",
        "pitch": 1.02,
        "rate": 0.96,
        "volume": 1.0,
        "tags": ["또렷", "명료", "여성"],
        "voice_hints": ["SunHi", "Heami", "Female", "여성", "Microsoft"],
    },
    "female_jieun_gentle": {
        "id": "female_jieun_gentle",
        "label": "박지은 · 잔잔한",
        "gender": "female",
        "counselor_id": "jieun",
        "pitch": 1.04,
        "rate": 0.86,
        "volume": 0.98,
        "tags": ["잔잔", "차분", "여성", "저속"],
        "voice_hints": ["Heami", "Yuna", "Female", "여성", "soft"],
    },
    "female_yuna_bright": {
        "id": "female_yuna_bright",
        "label": "최유나 · 밝은",
        "gender": "female",
        "counselor_id": "yuna",
        "pitch": 1.1,
        "rate": 1.02,
        "volume": 1.0,
        "tags": ["밝음", "지지", "여성", "활기"],
        "voice_hints": ["Yuna", "SunHi", "Female", "여성", "Google"],
    },
    "female_soyul_intimate": {
        "id": "female_soyul_intimate",
        "label": "한소율 · 속삭임",
        "gender": "female",
        "counselor_id": "soyul",
        "pitch": 1.08,
        "rate": 0.88,
        "volume": 0.92,
        "tags": ["친밀", "섬세", "여성", "저속"],
        "voice_hints": ["Heami", "Female", "여성", "soft", "gentle"],
    },
    "male_minjun_warm": {
        "id": "male_minjun_warm",
        "label": "김민준 · 따뜻한",
        "gender": "male",
        "counselor_id": "minjun",
        "pitch": 0.88,
        "rate": 0.92,
        "volume": 1.0,
        "tags": ["따뜻", "든든", "남성", "저속"],
        "voice_hints": ["InJoon", "Male", "남성", "Microsoft", "Google 한국의"],
    },
    "male_minjun_steady": {
        "id": "male_minjun_steady",
        "label": "김민준 · 안정적인",
        "gender": "male",
        "counselor_id": "minjun",
        "pitch": 0.85,
        "rate": 0.88,
        "volume": 1.0,
        "tags": ["안정", "중저음", "남성"],
        "voice_hints": ["InJoon", "Male", "남성", "deep"],
    },
    "male_junho_deep": {
        "id": "male_junho_deep",
        "label": "이준호 · 깊은",
        "gender": "male",
        "counselor_id": "junho",
        "pitch": 0.82,
        "rate": 0.86,
        "volume": 1.0,
        "tags": ["깊음", "차분", "남성", "저속"],
        "voice_hints": ["InJoon", "Male", "남성", "Microsoft", "low"],
    },
    "male_seojun_clear": {
        "id": "male_seojun_clear",
        "label": "박서준 · 명료한",
        "gender": "male",
        "counselor_id": "seojun",
        "pitch": 0.9,
        "rate": 0.98,
        "volume": 1.0,
        "tags": ["명료", "전문", "남성"],
        "voice_hints": ["Male", "남성", "Google", "InJoon"],
    },
    "male_woojin_friendly": {
        "id": "male_woojin_friendly",
        "label": "정우진 · 친근한",
        "gender": "male",
        "counselor_id": "woojin",
        "pitch": 0.94,
        "rate": 1.0,
        "volume": 1.0,
        "tags": ["친근", "편안", "남성"],
        "voice_hints": ["Male", "남성", "friendly", "Google 한국의"],
    },
}

DEFAULT_STYLE: Dict[str, Any] = {
    "counselor_id": "seoyeon",
    "texture": "warm",
    "tone": dict(DEFAULT_TONE),
    "voice_preset_id": "female_seoyeon_soft",
    "voice_enabled": True,
    "auto_speak": False,
}


def _clamp_tone(value: Any, default: int = 3) -> int:
    try:
        return max(1, min(5, int(value)))
    except (TypeError, ValueError):
        return default


def normalize_style(raw: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    source = deepcopy(DEFAULT_STYLE)
    if not raw:
        return source
    if raw.get("counselor_id") in COUNSELORS:
        source["counselor_id"] = raw["counselor_id"]
    if raw.get("texture") in TEXTURE_PRESETS:
        source["texture"] = raw["texture"]
    tone_in = raw.get("tone") or {}
    source["tone"] = {
        "warmth": _clamp_tone(tone_in.get("warmth"), DEFAULT_TONE["warmth"]),
        "formality": _clamp_tone(tone_in.get("formality"), DEFAULT_TONE["formality"]),
        "pace": _clamp_tone(tone_in.get("pace"), DEFAULT_TONE["pace"]),
        "directness": _clamp_tone(tone_in.get("directness"), DEFAULT_TONE["directness"]),
    }
    if raw.get("voice_preset_id") in VOICE_PRESETS:
        source["voice_preset_id"] = raw["voice_preset_id"]
    source["voice_enabled"] = bool(raw.get("voice_enabled", source["voice_enabled"]))
    source["auto_speak"] = bool(raw.get("auto_speak", source["auto_speak"]))
    counselor = COUNSELORS[source["counselor_id"]]
    preset = VOICE_PRESETS.get(source["voice_preset_id"])
    if not preset or preset["counselor_id"] != counselor["id"]:
        source["voice_preset_id"] = counselor["default_voice"]
    return source


def resolve_counseling_style(user_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    stored = (user_settings or {}).get("counseling_style") or {}
    style = normalize_style(stored)
    counselor = COUNSELORS[style["counselor_id"]]
    voice = VOICE_PRESETS[style["voice_preset_id"]]
    texture = TEXTURE_PRESETS[style["texture"]]
    return {
        **style,
        "counselor": counselor,
        "counselor_name": counselor["name"],
        "voice": voice,
        "texture_meta": texture,
    }


def build_style_system_block(style: Dict[str, Any]) -> str:
    resolved = style if style.get("counselor") else resolve_counseling_style({"counseling_style": style})
    counselor = resolved["counselor"]
    texture = resolved["texture_meta"]
    tone = resolved["tone"]
    voice = resolved["voice"]
    warmth_word = "매우 따뜻" if tone["warmth"] >= 4 else ("중립적" if tone["warmth"] == 3 else "차분·절제")
    formality_word = "격식 있게" if tone["formality"] >= 4 else ("반말에 가깝지 않은 편안함" if tone["formality"] <= 2 else "자연스럽게")
    pace_word = "느리고 여유롭게" if tone["pace"] <= 2 else ("보통 속도" if tone["pace"] == 3 else "약간 빠르게")
    direct_word = "직접적 조언은 최소화" if tone["directness"] <= 2 else ("균형" if tone["directness"] == 3 else "명확한 제안 가능")
    return (
        "## [필수] 사용자 맞춤 상담 톤·질감\n"
        f"- 상담사: **{counselor['name']}** ({counselor['title']}, {counselor['gender']})\n"
        f"- 질감: **{texture['label']}** — {texture['prompt']}\n"
        f"- 톤: 따뜻함 {tone['warmth']}/5 ({warmth_word}), "
        f"격식 {tone['formality']}/5 ({formality_word}), "
        f"속도 {tone['pace']}/5 ({pace_word}), "
        f"직접성 {tone['directness']}/5 ({direct_word})\n"
        f"- 음성 프리셋: {voice['label']} — 말투도 이 음성 느낌({', '.join(voice['tags'][:3])})에 맞추세요.\n"
        "- 사용자가 설정한 톤·질감을 **무시하지 마세요**. 다른 캐릭터처럼 말하지 마세요."
    )


def search_voice_presets(
    query: str = "",
    gender: Optional[str] = None,
    counselor_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = (query or "").strip().lower()
    results: List[Dict[str, Any]] = []
    for preset in VOICE_PRESETS.values():
        if gender and preset["gender"] != gender:
            continue
        if counselor_id and preset["counselor_id"] != counselor_id:
            continue
        haystack = " ".join(
            [
                preset["label"],
                preset["gender"],
                preset["counselor_id"],
                " ".join(preset.get("tags", [])),
                " ".join(preset.get("voice_hints", [])),
            ]
        ).lower()
        if q and q not in haystack:
            continue
        counselor = COUNSELORS[preset["counselor_id"]]
        results.append({**preset, "counselor_name": counselor["name"]})
    return sorted(results, key=lambda item: item["label"])


def build_style_catalog() -> Dict[str, Any]:
    return {
        "textures": [
            {"id": key, **value}
            for key, value in TEXTURE_PRESETS.items()
        ],
        "counselors": list(COUNSELORS.values()),
        "voice_presets": search_voice_presets(),
        "tone_axes": [
            {"id": "warmth", "label": "따뜻함", "low": "차분·절제", "high": "포근·수용"},
            {"id": "formality", "label": "격식", "low": "편안", "high": "전문·격식"},
            {"id": "pace", "label": "속도", "low": "느리게", "high": "빠르게"},
            {"id": "directness", "label": "직접성", "low": "탐색·질문", "high": "명확·제안"},
        ],
        "defaults": DEFAULT_STYLE,
    }
