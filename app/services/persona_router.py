from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models.clinical import ClinicalSchool, MoodState
from app.services.counseling_theories import (
    THEORY_CATALOG,
    build_theory_directive,
    get_theory_meta,
)
from app.services.instant_keyword_router import react_instantly

VULNERABLE_KEYWORDS = ("힘들", "울", "상처", "외로", "무너", "버텨", "지쳐", "슬프", "아프")
DEFENSIVE_KEYWORDS = ("항상", "어쩔 수", "괜찮", "부정", "억누", "숨기", "모르겠", "회피", "피하")
ANALYTICAL_KEYWORDS = ("생각", "논리", "이유", "왜", "분석", "판단", "틀렸", "실수", "실패")
DISTORTION_KEYWORDS = {
    "all_or_nothing": ("완전", "전부", "항상", "절대", "망했", "망가"),
    "overgeneralization": ("늘", "매번", "역시", "또", "모두"),
    "catastrophizing": ("끝", "망했", "최악", "불행", "큰일"),
    "rumination": ("반복", "계속", "머릿속", "떠올"),
    "emotional_reasoning": ("느끼니까", "기분상", "감정적으로", "느낌이"),
    "should_statements": ("해야 해", "해야만", "하면 안", "당연히"),
    "mind_reading": ("분명 생각", "나를 욕", "무시할 게"),
    "personalization": ("내 탓", "내 때문", "내가 망"),
}

PERSONA_CATALOG = {
    school: {
        "label": meta["label"],
        "short_label": meta["short_label"],
        "subtitle": meta["subtitle"],
        "category": meta["category"],
        "counselor_tone": meta["counselor_tone"],
        "techniques": meta["techniques"],
        "founder": meta["founder"],
    }
    for school, meta in THEORY_CATALOG.items()
}


def detect_cognitive_distortions(text: str) -> List[str]:
    """Psychology CBT-15 detector (shared entry used by persona router)."""
    try:
        from app.services.mode_analyzers import detect_cbt_15_distortions

        return detect_cbt_15_distortions(text)
    except Exception:
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
    counselor_default_school: Optional[ClinicalSchool] = None,
) -> Dict[str, Any]:
    mood = detect_mood_state(user_message, recent_messages)
    distortions = detect_cognitive_distortions(user_message)
    reaction = react_instantly(user_message, recent_messages, preferred_school=preferred_school)

    if preferred_school:
        school = preferred_school
        reason = "user_selected"
    elif reaction.reason == "crisis_keyword_instant":
        school = reaction.school
        reason = reaction.reason
    elif reaction.score > 0 and reaction.reason in {"instant_weighted_keyword", "user_selected"}:
        school = reaction.school
        reason = "instant_keyword_theory_match"
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
    elif counselor_default_school:
        school = counselor_default_school
        reason = "counselor_specialty_default"
    else:
        school = ClinicalSchool.INTEGRATIVE
        reason = "integrative_default"

    meta = get_theory_meta(school)
    techniques = list(reaction.techniques) if reaction.techniques else list(meta["techniques"])
    return {
        "school": school,
        "mood_state": mood,
        "reason": reason,
        "detected_distortions": distortions,
        "persona_label": meta["label"],
        "persona_subtitle": meta["subtitle"],
        "counselor_tone": meta["counselor_tone"],
        "techniques": techniques[:8],
        "category": meta["category"],
        "instant_reaction": reaction.to_dict(),
    }


def build_persona_directive(school: ClinicalSchool, distortions: Optional[List[str]] = None) -> str:
    return build_theory_directive(school, distortions)
