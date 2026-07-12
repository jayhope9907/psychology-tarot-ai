from __future__ import annotations

from typing import Any, Dict, List

from app.services.chat_session import ChatSessionState
from app.services.fatigue_manager import (
    detect_assessment_request,
    detect_counseling_request,
    detect_distress,
)

CONTEXT_KEYWORDS = (
    "회사",
    "직장",
    "학교",
    "가족",
    "연인",
    "친구",
    "부모",
    "밤",
    "아침",
    "주말",
    "집",
    "혼자",
    "사람",
    "관계",
    "대인",
)

DURATION_KEYWORDS = (
    "최근",
    "오래",
    "며칠",
    "몇달",
    "몇 달",
    "언제부터",
    "부터",
    "년",
    "개월",
    "일주",
    "한동안",
)

IMPACT_KEYWORDS = (
    "일상",
    "출근",
    "학업",
    "잠",
    "식사",
    "일",
    "생활",
    "지장",
    "못",
    "힘들",
    "버거",
    "무기력",
    "집중",
)

EMOTION_KEYWORDS = (
    "우울",
    "불안",
    "답답",
    "슬픔",
    "외로",
    "화",
    "짜증",
    "무기력",
    "공허",
    "두려",
    "초조",
    "스트레스",
)

RAPPORT_READY_THRESHOLD = 0.72
RAPPORT_MIN_TURNS = 3
RAPPORT_MIN_USER_MESSAGES = 2
RAPPORT_MIN_CHIEF_LENGTH = 16


def _user_messages(state: ChatSessionState, current_message: str = "") -> List[str]:
    parts = [
        (entry.get("content") or "").strip()
        for entry in state.messages
        if entry.get("role") == "user"
    ]
    if current_message.strip():
        parts.append(current_message.strip())
    return [part for part in parts if part]


def _substantive_user_turns(messages: List[str]) -> int:
    return sum(1 for message in messages if len(message) >= 10 or detect_distress(message))


def _match_any(text: str, keywords: tuple[str, ...]) -> List[str]:
    return [keyword for keyword in keywords if keyword in text]


def update_client_profile(state: ChatSessionState, user_message: str = "") -> Dict[str, Any]:
    notes = state.phase_notes
    profile: Dict[str, Any] = dict(notes.get("client_profile") or {})
    messages = _user_messages(state, user_message)
    combined = "\n".join(messages).lower()
    current = (user_message or "").strip()

    if not notes.get("chief_complaint"):
        best = max(messages, key=len, default="")
        if len(best) >= 8 or detect_distress(best):
            notes["chief_complaint"] = best[:240]
            profile["chief_complaint"] = notes["chief_complaint"]
    elif current and len(current) > len(profile.get("chief_complaint", "")):
        if detect_distress(current) or len(current) >= 12:
            notes["chief_complaint"] = current[:240]
            profile["chief_complaint"] = notes["chief_complaint"]

    emotions = set(profile.get("emotional_themes") or [])
    emotions.update(_match_any(combined, EMOTION_KEYWORDS))
    profile["emotional_themes"] = sorted(emotions)

    contexts = set(profile.get("context_themes") or [])
    contexts.update(_match_any(combined, CONTEXT_KEYWORDS))
    profile["context_themes"] = sorted(contexts)

    impacts = set(profile.get("impact_areas") or [])
    impacts.update(_match_any(combined, IMPACT_KEYWORDS))
    profile["impact_areas"] = sorted(impacts)

    duration_matches = _match_any(combined, DURATION_KEYWORDS)
    if duration_matches:
        profile["duration_hint"] = duration_matches[0]

    profile["help_intent"] = bool(
        profile.get("help_intent")
        or detect_counseling_request(combined)
        or detect_assessment_request(combined)
        or detect_assessment_request(user_message)
    )
    profile["substantive_user_turns"] = _substantive_user_turns(messages)
    profile["total_user_turns"] = len(messages)

    notes["client_profile"] = profile
    return profile


def rapport_readiness(state: ChatSessionState, user_message: str = "") -> Dict[str, Any]:
    profile = update_client_profile(state, user_message)
    chief = state.phase_notes.get("chief_complaint") or profile.get("chief_complaint") or ""

    checks = {
        "exchanges": profile.get("substantive_user_turns", 0) >= RAPPORT_MIN_USER_MESSAGES,
        "turn_depth": state.turn_count >= RAPPORT_MIN_TURNS,
        "chief_complaint": len(chief) >= RAPPORT_MIN_CHIEF_LENGTH,
        "emotion": len(profile.get("emotional_themes") or []) >= 1,
        "context": len(profile.get("context_themes") or []) >= 1,
        "impact_or_duration": bool(
            profile.get("duration_hint")
            or len(profile.get("impact_areas") or []) >= 1
        ),
    }

    weights = {
        "exchanges": 0.18,
        "turn_depth": 0.12,
        "chief_complaint": 0.22,
        "emotion": 0.18,
        "context": 0.15,
        "impact_or_duration": 0.15,
    }

    score = round(sum(weights[key] for key, ok in checks.items() if ok), 2)
    missing: List[str] = []

    if not checks["exchanges"]:
        missing.append("고객의 구체적 이야기를 2회 이상 더 들어주세요")
    if not checks["chief_complaint"]:
        missing.append("주호소(가장 힘든 마음)를 조금 더 구체적으로")
    if not checks["emotion"]:
        missing.append("지금 느껴지는 감정(우울·불안·답답함 등)")
    if not checks["context"]:
        missing.append("어떤 상황·관계에서 특히 힘든지")
    if not checks["impact_or_duration"]:
        missing.append("언제부터·일상에 어떤 지장이 있는지")
    if not checks["turn_depth"]:
        missing.append("충분한 라포(최소 3턴 대화)")

    ready = score >= RAPPORT_READY_THRESHOLD and all(
        [
            checks["exchanges"],
            checks["turn_depth"],
            checks["chief_complaint"],
            checks["emotion"],
            checks["context"],
            checks["impact_or_duration"],
        ]
    )

    explicit_request = detect_assessment_request(user_message) and checks["chief_complaint"] and checks["emotion"]
    if explicit_request and checks["exchanges"] and state.turn_count >= 2:
        ready = ready or (
            checks["chief_complaint"]
            and checks["emotion"]
            and profile.get("substantive_user_turns", 0) >= 2
            and score >= 0.58
        )

    return {
        "score": score,
        "ready": ready,
        "threshold": RAPPORT_READY_THRESHOLD,
        "checks": checks,
        "missing": missing,
        "profile_summary": _profile_summary(profile, chief),
        "client_profile": profile,
    }


def is_rapport_complete(state: ChatSessionState, user_message: str = "") -> bool:
    return rapport_readiness(state, user_message)["ready"]


def _profile_summary(profile: Dict[str, Any], chief: str) -> str:
    parts = [f"주호소: {chief[:80]}"] if chief else []
    if profile.get("emotional_themes"):
        parts.append("감정: " + ", ".join(profile["emotional_themes"][:3]))
    if profile.get("context_themes"):
        parts.append("맥락: " + ", ".join(profile["context_themes"][:3]))
    if profile.get("duration_hint"):
        parts.append(f"기간 단서: {profile['duration_hint']}")
    if profile.get("impact_areas"):
        parts.append("영향: " + ", ".join(profile["impact_areas"][:3]))
    return " · ".join(parts) if parts else "고객 파악 진행 중"


def rapport_phase_prompt(state: ChatSessionState, user_message: str = "") -> str:
    from app.services.gentle_reflection import gentle_reflection_system_block

    readiness = rapport_readiness(state, user_message)
    base = (
        "## 현재 상담 단계: 관계 형성·고객 파악 (초기)\n"
        "- 비판단·수용적 태도로 안전한 대화 공간을 만드세요.\n"
        "- **검사·케이스 분류·결제 안내는 고객 파악이 충분히 끝난 뒤**에만 진행합니다.\n"
        f"- 고객 파악 진행도: {int(readiness['score'] * 100)}% "
        f"(목표 {int(readiness['threshold'] * 100)}%)\n"
    )
    base += "\n" + gentle_reflection_system_block(state, user_message)

    if readiness["ready"]:
        base += (
            "- 고객 파악이 충분합니다. 자연스럽게 검사 패키지 안내로 넘어갈 수 있습니다.\n"
            f"- 파악 요약: {readiness['profile_summary']}\n"
        )
        return base

    missing_text = " / ".join(readiness["missing"][:3])
    base += (
        f"- 아직 부족한 파악: {missing_text}\n"
        "- 위 항목을 **한 번에 하나씩** 부드럽게 탐색하세요. 설문조사처럼 연속 질문하지 마세요.\n"
        "- 해결책·진단·검사를 서두르지 말고, 감정 반영 후 개방형 질문 1개로 마무리하세요.\n"
        "- ‘지금 기분 어떠세요?’ ‘대인관계는요?’처럼 직접 묻기보다, "
        "「제가 봤을 때는… 힘들어 보이시네요」관찰 문장으로 풀어 가세요.\n"
    )
    if readiness["profile_summary"] != "고객 파악 진행 중":
        base += f"- 지금까지 파악: {readiness['profile_summary']}\n"
    return base
