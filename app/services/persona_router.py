from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models.clinical import ClinicalSchool, MoodState

VULNERABLE_KEYWORDS = ("힘들", "울", "상처", "외로", "무너", "버텨", "지쳐", "슬프", "아프")
DEFENSIVE_KEYWORDS = ("항상", "어쩔 수", "괜찮", "부정", "억누", "숨기", "모르겠", "회피", "피하")
ANALYTICAL_KEYWORDS = ("생각", "논리", "이유", "왜", "분석", "판단", "틀렸", "실수", "실패")
DISTORTION_KEYWORDS = {
    "all_or_nothing": ("완전", "전부", "항상", "절대", "망했", "망가"),
    "overgeneralization": ("늘", "매번", "역시", "또", "모두"),
    "catastrophizing": ("끝", "망했", "최악", "불행", "큰일"),
    "rumination": ("반복", "계속", "머릿속", "떠올"),
}

PERSONA_CATALOG = {
    ClinicalSchool.FREUDIAN: {
        "label": "무의식 직면 모드",
        "subtitle": "프로이트 학파 · 방어기제와 그림자 탐색",
        "counselor_tone": "날카롭지만 존중하는 통찰",
    },
    ClinicalSchool.ROGERIAN: {
        "label": "인간중심 수용 모드",
        "subtitle": "칼 로저스 학파 · 무조건적 긍정적 존중",
        "counselor_tone": "따뜻한 공감과 수용",
    },
    ClinicalSchool.BECK_CBT: {
        "label": "인지 왜곡 교정 모드",
        "subtitle": "아론 벡 학파 · 소크라테스식 질문",
        "counselor_tone": "논리적이고 협력적인 재구조화",
    },
}


def detect_cognitive_distortions(text: str) -> List[str]:
    normalized = (text or "").lower()
    detected: List[str] = []
    for distortion, keywords in DISTORTION_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            detected.append(distortion)
    return detected


def detect_mood_state(user_message: str, recent_messages: Optional[List[Dict[str, str]]] = None) -> MoodState:
    corpus = " ".join([user_message] + [entry.get("content", "") for entry in (recent_messages or [])[-4:]]).lower()

    if any(keyword in corpus for keyword in DEFENSIVE_KEYWORDS):
        return MoodState.DEFENSIVE
    if detect_cognitive_distortions(corpus):
        return MoodState.ANALYTICAL
    if any(keyword in corpus for keyword in VULNERABLE_KEYWORDS):
        return MoodState.VULNERABLE
    if any(keyword in corpus for keyword in ANALYTICAL_KEYWORDS):
        return MoodState.ANALYTICAL
    return MoodState.NEUTRAL


def route_clinical_persona(
    user_message: str,
    preferred_school: Optional[ClinicalSchool] = None,
    recent_messages: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    mood = detect_mood_state(user_message, recent_messages)
    distortions = detect_cognitive_distortions(user_message)

    if preferred_school:
        school = preferred_school
        reason = "user_selected"
    elif distortions and mood in {MoodState.ANALYTICAL, MoodState.DEFENSIVE}:
        school = ClinicalSchool.BECK_CBT
        reason = "cognitive_distortion_signal"
    elif mood == MoodState.DEFENSIVE:
        school = ClinicalSchool.FREUDIAN
        reason = "defensive_pattern_signal"
    elif mood == MoodState.VULNERABLE:
        school = ClinicalSchool.ROGERIAN
        reason = "vulnerable_affect_signal"
    elif mood == MoodState.ANALYTICAL:
        school = ClinicalSchool.BECK_CBT
        reason = "analytical_processing_signal"
    else:
        school = ClinicalSchool.ROGERIAN
        reason = "default_supportive"

    catalog = PERSONA_CATALOG[school]
    return {
        "school": school,
        "mood_state": mood,
        "reason": reason,
        "detected_distortions": distortions,
        "persona_label": catalog["label"],
        "persona_subtitle": catalog["subtitle"],
        "counselor_tone": catalog["counselor_tone"],
    }


def build_persona_directive(school: ClinicalSchool, distortions: Optional[List[str]] = None) -> str:
    distortions = distortions or []
    if school == ClinicalSchool.FREUDIAN:
        return (
            "## 임상 페르소나: 프로이트 학파 (무의식 직면 모드)\n"
            "- 방어기제, 반복 패턴, 억압된 감정의 '그림자'를 날카롭지만 존중하는 통찰로 짚으세요.\n"
            "- 표면 핑계 아래 숨은 욕구·두려움·미해결 갈등을 탐색하세요.\n"
            "- 단정적 진단은 금지하되, 회피하고 있는 진실을 부드럽게 마주하게 하세요."
        )
    if school == ClinicalSchool.BECK_CBT:
        distortion_hint = ", ".join(distortions) if distortions else "일반적 자동적 사고"
        return (
            "## 임상 페르소나: 아론 벡 학파 (인지 왜곡 교정 모드)\n"
            f"- 포착된 왜곡 징후: {distortion_hint}\n"
            "- 소크라테스식 질문으로 증거·대안·균형 관점을 탐색하세요.\n"
            "- '그 생각이 100% 사실이라는 근거는 무엇인가요?' 같은 협력적 질문을 사용하세요.\n"
            "- 감정을 무시하지 말되, 사고 재구조화와 작은 행동 실험으로 연결하세요."
        )
    return (
        "## 임상 페르소나: 칼 로저스 학파 (인간중심 수용 모드)\n"
        "- '그랬군요, 많이 힘드셨겠습니다'처럼 무조건적 긍정적 존중을 보여주세요.\n"
        "- 조언보다 반영·공감·수용을 우선하고, 내담자가 스스로 답을 찾도록 지지하세요.\n"
        "- 판단·교정·해석을 최소화하고, 지금 느끼는 감정의 안전한 표현을 돕세요."
    )
