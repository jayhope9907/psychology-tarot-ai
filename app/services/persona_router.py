from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models.clinical import ClinicalSchool, MoodState
from app.services.counseling_theories import (
    THEORY_CATALOG,
    build_theory_directive,
    get_theory_meta,
)

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


def _match_theory_by_keywords(corpus: str) -> Optional[ClinicalSchool]:
    best_school: Optional[ClinicalSchool] = None
    best_score = 0
    for school, meta in THEORY_CATALOG.items():
        if school == ClinicalSchool.INTEGRATIVE:
            continue
        keywords = meta.get("routing_keywords") or ()
        score = sum(1 for keyword in keywords if keyword in corpus)
        if score > best_score:
            best_score = score
            best_school = school
    return best_school if best_score > 0 else None


def route_clinical_persona(
    user_message: str,
    preferred_school: Optional[ClinicalSchool] = None,
    recent_messages: Optional[List[Dict[str, str]]] = None,
    counselor_default_school: Optional[ClinicalSchool] = None,
) -> Dict[str, Any]:
    mood = detect_mood_state(user_message, recent_messages)
    distortions = detect_cognitive_distortions(user_message)
    corpus = " ".join([user_message] + [entry.get("content", "") for entry in (recent_messages or [])[-4:]]).lower()

    if preferred_school:
        school = preferred_school
        reason = "user_selected"
    else:
        keyword_match = _match_theory_by_keywords(corpus)
        if keyword_match:
            school = keyword_match
            reason = "keyword_theory_match"
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
    return {
        "school": school,
        "mood_state": mood,
        "reason": reason,
        "detected_distortions": distortions,
        "persona_label": meta["label"],
        "persona_subtitle": meta["subtitle"],
        "counselor_tone": meta["counselor_tone"],
        "techniques": meta["techniques"],
        "category": meta["category"],
    }


def build_persona_directive(school: ClinicalSchool, distortions: Optional[List[str]] = None) -> str:
    return build_theory_directive(school, distortions)
