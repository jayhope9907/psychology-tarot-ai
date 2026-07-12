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
        "title": "인간중심·로저스학파 AI 상담 가이드",
        "tagline": "무조건적 수용 · 깊은 공감",
        "primary_school": "ROGERIAN",
        "secondary_schools": ["EFT", "INTEGRATIVE"],
        "techniques": ["감정 반영", "재진술", "적극적 경청", "내재적 동기"],
        "bio": "상담심리학·인간중심치료 훈련 기반. 수용과 공감을 중심으로 내담자 고유의 성장 가능성을 함께 탐색합니다.",
        "default_voice": "female_seoyeon_soft",
        "default_texture": "warm",
    },
    "jieun": {
        "id": "jieun",
        "name": "박지은",
        "gender": "female",
        "title": "게슈탈트·마음챙김 AI 상담 가이드",
        "tagline": "지금-여기 알아차림 · 빈 의자",
        "primary_school": "GESTALT",
        "secondary_schools": ["MINDFULNESS", "PSYCHODRAMA"],
        "techniques": ["지금-여기 초점", "빈 의자 기법", "신체 감각", "역할 바꾸기"],
        "bio": "게슈탈트·마음챙김 통합 훈련. 말이 어려울 때는 빈 의자·역할로 지금 경험을 함께 살펴봅니다.",
        "default_voice": "female_jieun_gentle",
        "default_texture": "calm",
    },
    "nari": {
        "id": "nari",
        "name": "김나리",
        "gender": "female",
        "title": "사이코드라마·연극치료 AI 가이드",
        "tagline": "역할극 · 장면 · 상징 표현",
        "primary_school": "PSYCHODRAMA",
        "secondary_schools": ["DRAMA_THERAPY", "GESTALT"],
        "techniques": ["역할극", "역할 바꾸기", "더블링", "상징 표현", "탈역할"],
        "bio": "모레노 사이코드라마·연극치료 교육 기반. 말·글이 힘든 내담자와 역할·장면으로 안전하게 표현을 돕습니다.",
        "default_voice": "female_nari_warm",
        "default_texture": "warm",
    },
    "bora": {
        "id": "bora",
        "name": "이보라",
        "gender": "female",
        "title": "미술치료·표현예술 AI 가이드",
        "tagline": "낙서 · 만다라 · 색채 표현",
        "primary_school": "ART_THERAPY",
        "secondary_schools": ["JUNGIAN", "TRAUMA_INFORMED"],
        "techniques": ["자유화", "낙서 기법", "만다라", "콜라주", "작품 대화"],
        "bio": "나움버그·크래머·말키오디 미술치료 교육 기반. 말 대신 선·색·형태로 마음을 안전하게 표현하도록 돕습니다.",
        "default_voice": "female_bora_soft",
        "default_texture": "warm",
    },
    "yuna": {
        "id": "yuna",
        "name": "최유나",
        "gender": "female",
        "title": "해결중심·동기강화 AI 상담 가이드",
        "tagline": "강점 탐색 · 변화 대화",
        "primary_school": "SOLUTION_FOCUSED",
        "secondary_schools": ["MOTIVATIONAL", "REALITY_THERAPY"],
        "techniques": ["기적 질문", "예외 탐색", "OARS", "다음 작은 단계"],
        "bio": "해결중심·동기강화상담 훈련. 문제보다 가능성과 이미 있는 자원에 초점을 둡니다.",
        "default_voice": "female_yuna_bright",
        "default_texture": "energetic",
    },
    "soyul": {
        "id": "soyul",
        "name": "한소율",
        "gender": "female",
        "title": "감정중심·서사 AI 상담 가이드",
        "tagline": "애착 감정 · 이야기 재구성",
        "primary_school": "EFT",
        "secondary_schools": ["NARRATIVE", "IPT"],
        "techniques": ["1차 감정 탐색", "애착 욕구", "문제 외화", "감정 명명"],
        "bio": "감정중심·서사치료 훈련. 관계 속 감정과 자신의 이야기를 섬세하게 함께 풀어갑니다.",
        "default_voice": "female_soyul_intimate",
        "default_texture": "intimate",
    },
    "haneul": {
        "id": "haneul",
        "name": "김하늘",
        "gender": "female",
        "title": "DBT·감정조절 AI 상담 가이드",
        "tagline": "수용과 변화 · 고통감내",
        "primary_school": "DBT",
        "secondary_schools": ["BECK_CBT", "MINDFULNESS"],
        "techniques": ["감정조절", "고통감내", "마음챙김", "대인효과성"],
        "bio": "弁증법행동치료(DBT) 훈련. 감정의 파도 속에서도 균형과 기술을 함께 연습합니다.",
        "default_voice": "female_haneul_calm",
        "default_texture": "calm",
    },
    "seoa": {
        "id": "seoa",
        "name": "윤서아",
        "gender": "female",
        "title": "대인관계·체계 AI 상담 가이드",
        "tagline": "관계 패턴 · 가족체계",
        "primary_school": "IPT",
        "secondary_schools": ["BOWEN_SYSTEMS", "NARRATIVE"],
        "techniques": ["관계 패턴", "역할 전환", "가계도", "애도"],
        "bio": "대인관계치료·가족체계 훈련. 증상을 관계와 역할 맥락에서 함께 이해합니다.",
        "default_voice": "female_seoa_clear",
        "default_texture": "professional",
    },
    "minjun": {
        "id": "minjun",
        "name": "김민준",
        "gender": "male",
        "title": "인간중심·통합 AI 상담 가이드",
        "tagline": "든든한 수용 · 유연한 통합",
        "primary_school": "INTEGRATIVE",
        "secondary_schools": ["ROGERIAN", "SOLUTION_FOCUSED"],
        "techniques": ["공감적 경청", "상황별 기법", "요약·반영", "공통 요인"],
        "bio": "상담심리학·통합상담 훈련. 상황에 맞는 기법을 유연하게 선택해 함께합니다.",
        "default_voice": "male_minjun_warm",
        "default_texture": "warm",
    },
    "junho": {
        "id": "junho",
        "name": "이준호",
        "gender": "male",
        "title": "정신분석·융 AI 상담 가이드",
        "tagline": "무의식·원형 · 깊은 통찰",
        "primary_school": "FREUDIAN",
        "secondary_schools": ["JUNGIAN", "ADLERIAN"],
        "techniques": ["방어기제", "반복 패턴", "상징·꿈", "그림자 탐색"],
        "bio": "정신분석·분석심리 훈련. 표면 아래 패턴과 상징을 존중하며 탐색합니다.",
        "default_voice": "male_junho_deep",
        "default_texture": "calm",
    },
    "seojun": {
        "id": "seojun",
        "name": "박서준",
        "gender": "male",
        "title": "CBT·DBT AI 상담 가이드",
        "tagline": "인지 재구조화 · 행동 실험",
        "primary_school": "BECK_CBT",
        "secondary_schools": ["DBT", "REALITY_THERAPY"],
        "techniques": ["소크라테스식 질문", "사고 기록", "행동 활성화", "감정조절"],
        "bio": "인지행동·DBT 훈련. 생각·감정·행동의 연결을 구조적으로 함께 살펴봅니다.",
        "default_voice": "male_seojun_clear",
        "default_texture": "professional",
    },
    "woojin": {
        "id": "woojin",
        "name": "정우진",
        "gender": "male",
        "title": "ACT·현실치료 AI 상담 가이드",
        "tagline": "가치·수용 · 선택과 책임",
        "primary_school": "ACT",
        "secondary_schools": ["REALITY_THERAPY", "MOTIVATIONAL"],
        "techniques": ["가치 명료화", "인지 탈융합", "전념 행동", "WDEP"],
        "bio": "ACT·현실치료 훈련. 회피보다 가치에 맞는 행동과 선택을 함께 모색합니다.",
        "default_voice": "male_woojin_friendly",
        "default_texture": "intimate",
    },
    "doheon": {
        "id": "doheon",
        "name": "강도헌",
        "gender": "male",
        "title": "실존·의미 AI 상담 가이드",
        "tagline": "의미 탐색 · 진정성",
        "primary_school": "EXISTENTIAL",
        "secondary_schools": ["NARRATIVE", "ROGERIAN"],
        "techniques": ["의미 탐색", "선택과 책임", "궁규적 관심", "고립·불안 직면"],
        "bio": "실존주의 상담 훈련. 고통 속에서도 삶의 의미와 선택을 함께 질문합니다.",
        "default_voice": "male_doheon_deep",
        "default_texture": "calm",
    },
    "jaemin": {
        "id": "jaemin",
        "name": "한재민",
        "gender": "male",
        "title": "아들러·개별심리 AI 상담 가이드",
        "tagline": "용기 · 소속감 · 목표",
        "primary_school": "ADLERIAN",
        "secondary_schools": ["SOLUTION_FOCUSED", "REALITY_THERAPY"],
        "techniques": ["생활양식", "열등감·보상", "사회적 관심", "용기 격려"],
        "bio": "아들러 개별심리 훈련. 열등감과 소속, 목표를 현실적으로 함께 재설정합니다.",
        "default_voice": "male_jaemin_steady",
        "default_texture": "warm",
    },
    "taemin": {
        "id": "taemin",
        "name": "오태민",
        "gender": "male",
        "title": "대인·가족체계 AI 상담 가이드",
        "tagline": "관계 갈등 · 자기분화",
        "primary_school": "BOWEN_SYSTEMS",
        "secondary_schools": ["IPT", "NARRATIVE"],
        "techniques": ["자기분화", "삼각관계", "가계도", "대인 갈등"],
        "bio": "가족체계·대인관계치료 훈련. 관계 패턴과 역할을 체계적으로 함께 봅니다.",
        "default_voice": "male_taemin_clear",
        "default_texture": "professional",
    },
    "yoonseok": {
        "id": "yoonseok",
        "name": "송윤석",
        "gender": "male",
        "title": "트라우마·안전 AI 상담 가이드",
        "tagline": "안전 우선 · GROUNDING",
        "primary_school": "TRAUMA_INFORMED",
        "secondary_schools": ["EFT", "MINDFULNESS"],
        "techniques": ["안전 확보", "GROUNDING", "자원 강화", "선택권 존중"],
        "bio": "트라우마 정보 상담 훈련. 안전과 속도를 존중하며 천천히 회복을 함께합니다.",
        "default_voice": "male_yoonseok_soft",
        "default_texture": "calm",
    },
}

USER_COUNSELOR_LABELS: Dict[str, Dict[str, str]] = {
    "seoyeon": {"user_title": "마음 나눔 상담", "user_specialty": "따뜻한 공감·수용"},
    "jieun": {"user_title": "지금 마음 상담", "user_specialty": "빈 의자·알아차림"},
    "nari": {"user_title": "역할·표현 상담", "user_specialty": "역할극·연극 표현"},
    "bora": {"user_title": "미술·표현 상담", "user_specialty": "낙서·만다라·색채"},
    "yuna": {"user_title": "해결 찾기 상담", "user_specialty": "희망·강점 탐색"},
    "soyul": {"user_title": "감정·관계 상담", "user_specialty": "섬세한 감정 돌봄"},
    "haneul": {"user_title": "감정조절 상담", "user_specialty": "균형·안정"},
    "seoa": {"user_title": "대인·가족 상담", "user_specialty": "관계·가족 패턴"},
    "minjun": {"user_title": "맞춤 상담", "user_specialty": "든든한 동행"},
    "junho": {"user_title": "깊은 대화 상담", "user_specialty": "통찰·패턴 탐색"},
    "seojun": {"user_title": "생각 정리 상담", "user_specialty": "명확한 계획"},
    "woojin": {"user_title": "가치·실천 상담", "user_specialty": "편안한 실행"},
    "doheon": {"user_title": "의미 찾기 상담", "user_specialty": "삶의 의미·선택"},
    "jaemin": {"user_title": "용기·목표 상담", "user_specialty": "자신감·소속감"},
    "taemin": {"user_title": "가족상담", "user_specialty": "관계·역할 이해"},
    "yoonseok": {"user_title": "마음 회복 상담", "user_specialty": "안전·회복"},
}


def _public_counselor(raw: Dict[str, Any]) -> Dict[str, Any]:
    user = USER_COUNSELOR_LABELS.get(raw["id"], {})
    return {**raw, **user}


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
    "female_nari_warm": {
        "id": "female_nari_warm",
        "label": "김나리 · 따뜻한 표현",
        "gender": "female",
        "counselor_id": "nari",
        "pitch": 1.05,
        "rate": 0.94,
        "volume": 1.0,
        "tags": ["따뜻", "표현", "역할", "여성"],
        "voice_hints": ["Yuna", "SunHi", "Female", "여성", "Google"],
    },
    "female_bora_soft": {
        "id": "female_bora_soft",
        "label": "이보라 · 부드러운 미술",
        "gender": "female",
        "counselor_id": "bora",
        "pitch": 1.03,
        "rate": 0.9,
        "volume": 0.98,
        "tags": ["부드러움", "미술", "표현", "여성"],
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
    "female_haneul_calm": {
        "id": "female_haneul_calm",
        "label": "김하늘 · 차분한",
        "gender": "female",
        "counselor_id": "haneul",
        "pitch": 1.03,
        "rate": 0.88,
        "volume": 0.98,
        "tags": ["차분", "안정", "여성"],
        "voice_hints": ["Heami", "Female", "여성", "soft"],
    },
    "female_seoa_clear": {
        "id": "female_seoa_clear",
        "label": "윤서아 · 명료한",
        "gender": "female",
        "counselor_id": "seoa",
        "pitch": 1.0,
        "rate": 0.95,
        "volume": 1.0,
        "tags": ["명료", "전문", "여성"],
        "voice_hints": ["SunHi", "Female", "여성", "Microsoft"],
    },
    "male_doheon_deep": {
        "id": "male_doheon_deep",
        "label": "강도헌 · 깊은",
        "gender": "male",
        "counselor_id": "doheon",
        "pitch": 0.84,
        "rate": 0.85,
        "volume": 1.0,
        "tags": ["깊음", "실존", "남성"],
        "voice_hints": ["InJoon", "Male", "남성", "deep"],
    },
    "male_jaemin_steady": {
        "id": "male_jaemin_steady",
        "label": "한재민 · 안정적인",
        "gender": "male",
        "counselor_id": "jaemin",
        "pitch": 0.87,
        "rate": 0.9,
        "volume": 1.0,
        "tags": ["안정", "격려", "남성"],
        "voice_hints": ["InJoon", "Male", "남성", "steady"],
    },
    "male_taemin_clear": {
        "id": "male_taemin_clear",
        "label": "오태민 · 명료한",
        "gender": "male",
        "counselor_id": "taemin",
        "pitch": 0.89,
        "rate": 0.94,
        "volume": 1.0,
        "tags": ["명료", "체계", "남성"],
        "voice_hints": ["Male", "남성", "Google", "clear"],
    },
    "male_yoonseok_soft": {
        "id": "male_yoonseok_soft",
        "label": "송윤석 · 부드러운",
        "gender": "male",
        "counselor_id": "yoonseok",
        "pitch": 0.86,
        "rate": 0.84,
        "volume": 0.96,
        "tags": ["부드러움", "안전", "남성", "저속"],
        "voice_hints": ["Male", "남성", "soft", "gentle"],
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
    counselor = _public_counselor(COUNSELORS[style["counselor_id"]])
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
    from app.models.clinical import ClinicalSchool
    from app.services.counseling_theories import build_theory_directive, get_theory_meta

    resolved = style if style.get("counselor") else resolve_counseling_style({"counseling_style": style})
    counselor = resolved["counselor"]
    texture = resolved["texture_meta"]
    tone = resolved["tone"]
    voice = resolved["voice"]
    warmth_word = "매우 따뜻" if tone["warmth"] >= 4 else ("중립적" if tone["warmth"] == 3 else "차분·절제")
    formality_word = "격식 있게" if tone["formality"] >= 4 else ("반말에 가깝지 않은 편안함" if tone["formality"] <= 2 else "자연스럽게")
    pace_word = "느리고 여유롭게" if tone["pace"] <= 2 else ("보통 속도" if tone["pace"] == 3 else "약간 빠르게")
    direct_word = "직접적 조언은 최소화" if tone["directness"] <= 2 else ("균형" if tone["directness"] == 3 else "명확한 제안 가능")

    primary = counselor.get("primary_school", "INTEGRATIVE")
    try:
        school = ClinicalSchool(primary)
        theory_meta = get_theory_meta(school)
        theory_block = build_theory_directive(school)
    except ValueError:
        theory_meta = get_theory_meta(ClinicalSchool.INTEGRATIVE)
        theory_block = build_theory_directive(ClinicalSchool.INTEGRATIVE)

    secondary = counselor.get("secondary_schools") or []
    techniques = counselor.get("techniques") or theory_meta["techniques"][:4]
    bio = counselor.get("bio", "")

    return (
        "## [필수] 전문 상담 가이드 정체성\n"
        f"- 가이드: **{counselor['name']}** · {counselor['title']}\n"
        f"- 전문 영역: {theory_meta['label']} (+ {', '.join(secondary[:2]) if secondary else '통합'})\n"
        f"- 핵심 기법: {', '.join(techniques)}\n"
        f"- 소개: {bio}\n"
        f"{theory_block}\n"
        "## [필수] 사용자 맞춤 톤·질감\n"
        f"- 질감: **{texture['label']}** — {texture['prompt']}\n"
        f"- 톤: 따뜻함 {tone['warmth']}/5 ({warmth_word}), "
        f"격식 {tone['formality']}/5 ({formality_word}), "
        f"속도 {tone['pace']}/5 ({pace_word}), "
        f"직접성 {tone['directness']}/5 ({direct_word})\n"
        f"- 음성: {voice['label']} — 말투도 이 음성 느낌({', '.join(voice['tags'][:3])})에 맞추세요.\n"
        "- 설정한 가이드·이론·톤을 **무시하지 마세요**. 다른 캐릭터처럼 말하지 마세요."
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
    from app.services.counseling_theories import list_categories_for_api, list_theories_for_api

    return {
        "textures": [
            {"id": key, **value}
            for key, value in TEXTURE_PRESETS.items()
        ],
        "counselors": [_public_counselor(c) for c in COUNSELORS.values()],
        "theories": list_theories_for_api(),
        "theory_categories": list_categories_for_api(),
        "voice_presets": search_voice_presets(),
        "tone_axes": [
            {"id": "warmth", "label": "따뜻함", "low": "차분·절제", "high": "포근·수용"},
            {"id": "formality", "label": "격식", "low": "편안", "high": "전문·격식"},
            {"id": "pace", "label": "속도", "low": "느리게", "high": "빠르게"},
            {"id": "directness", "label": "직접성", "low": "탐색·질문", "high": "명확·제안"},
        ],
        "defaults": DEFAULT_STYLE,
    }
