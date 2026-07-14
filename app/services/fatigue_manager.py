from __future__ import annotations

from typing import Any, Dict

from app.services.chat_session import ChatSessionState

DISTRESS_KEYWORDS = (
    "불안",
    "우울",
    "우울증",
    "스트레스",
    "초조",
    "무기력",
    "상실",
    "두려움",
    "두려",
    "긴장",
    "외로움",
    "답답",
    "공허",
    "지침",
    "지쳤",
    "힘들",
    "힘드",
    "버거",
    "무서",
    "무감각",
    "슬픔",
)
COUNSELING_REQUEST_KEYWORDS = (
    "상담",
    "도와",
    "조언",
    "이야기",
    "힘들",
    "어떻게",
    "방법",
    "도움",
    "나누",
    "들어",
)
ASSESSMENT_REQUEST_KEYWORDS = (
    "검사",
    "테스트",
    "체크",
    "측정",
    "진단",
    "스크리닝",
    "확인해",
    "알아보",
    "평가",
    "가능한가",
    "가능해",
    "해줄",
    "해 주",
)
RELATIONSHIP_KEYWORDS = ("관계", "대인", "친구", "연인", "가족", "사람")

MAX_ASSESSMENTS_PER_SESSION = 3
WARMUP_TURNS = 1
MIN_TURNS_BETWEEN_ASSESSMENTS = 1
FATIGUE_BLOCK_THRESHOLD = 0.72


def _normalized(text: str) -> str:
    return (text or "").lower().strip()


def _text_includes_any(text: str, keywords: tuple[str, ...]) -> bool:
    normalized = _normalized(text)
    return any(keyword in normalized for keyword in keywords)


def compute_fatigue(state: ChatSessionState, user_message: str = "") -> float:
    fatigue = state.fatigue_score
    fatigue += state.assessments_offered * 0.12
    fatigue += max(0, state.assessments_offered - state.assessments_completed) * 0.1
    fatigue += state.assessments_skipped * 0.08

    if state.pending_assessment:
        fatigue += 0.1

    if len(user_message) > 180:
        fatigue += 0.08

    if state.turn_count > 0 and state.assessments_offered == 0:
        fatigue -= 0.05

    return round(min(1.0, max(0.0, fatigue)), 2)


def completion_rate(state: ChatSessionState) -> float:
    offered = max(1, state.assessments_offered)
    return round(state.assessments_completed / offered, 2)


def fatigue_snapshot(state: ChatSessionState, user_message: str = "") -> Dict[str, Any]:
    fatigue = compute_fatigue(state, user_message)
    state.fatigue_score = fatigue
    return {
        "fatigue_score": fatigue,
        "completion_rate": completion_rate(state) if state.assessments_offered else 1.0,
        "assessments_offered": state.assessments_offered,
        "assessments_completed": state.assessments_completed,
        "assessments_skipped": state.assessments_skipped,
        "blocked": fatigue >= FATIGUE_BLOCK_THRESHOLD,
    }


def detect_distress(user_message: str) -> bool:
    return _text_includes_any(user_message, DISTRESS_KEYWORDS)


def detect_counseling_request(user_message: str) -> bool:
    return _text_includes_any(user_message, COUNSELING_REQUEST_KEYWORDS)


def detect_assessment_request(user_message: str) -> bool:
    return _text_includes_any(user_message, ASSESSMENT_REQUEST_KEYWORDS)


def session_clinical_context(state: ChatSessionState, user_message: str = "") -> str:
    parts = [entry.get("content", "") for entry in state.messages[-8:]]
    parts.append(user_message)
    return "\n".join(part for part in parts if part)


def session_has_distress(state: ChatSessionState, user_message: str = "") -> bool:
    return detect_distress(session_clinical_context(state, user_message))


def session_has_assessment_intent(state: ChatSessionState, user_message: str = "") -> bool:
    context = session_clinical_context(state, user_message)
    return detect_assessment_request(context) or detect_assessment_request(user_message)


def _bypass_warmup(state: ChatSessionState, user_message: str) -> bool:
    if state.turn_count > WARMUP_TURNS:
        return True
    if detect_assessment_request(user_message):
        return True
    if detect_distress(user_message):
        return True
    if session_has_distress(state, user_message):
        return True
    return False


def _bypass_spacing(state: ChatSessionState, user_message: str) -> bool:
    return detect_assessment_request(user_message) or session_has_assessment_intent(state, user_message)


def should_block_new_assessment(state: ChatSessionState, user_message: str) -> bool:
    fatigue = compute_fatigue(state, user_message)
    state.fatigue_score = fatigue

    if state.pending_assessment:
        return True
    if state.assessments_offered >= MAX_ASSESSMENTS_PER_SESSION:
        return True

    if detect_assessment_request(user_message):
        return False

    if not _bypass_warmup(state, user_message):
        return True

    if (
        state.assessments_offered > 0
        and (state.turn_count - state.last_assessment_turn) < MIN_TURNS_BETWEEN_ASSESSMENTS
        and not _bypass_spacing(state, user_message)
    ):
        return True

    if fatigue >= FATIGUE_BLOCK_THRESHOLD and not detect_assessment_request(user_message):
        return True

    return False
