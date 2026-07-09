from __future__ import annotations

from typing import Any, Dict

from app.services.chat_session import ChatSessionState

DISTRESS_KEYWORDS = ("불안", "우울", "스트레스", "초조", "무기력", "상실", "두려움", "긴장", "외로움")
COUNSELING_REQUEST_KEYWORDS = ("상담", "도와", "조언", "이야기", "힘들", "어떻게", "방법", "도움", "나누", "들어")
MAX_ASSESSMENTS_PER_SESSION = 3
WARMUP_TURNS = 2
MIN_TURNS_BETWEEN_ASSESSMENTS = 2
FATIGUE_BLOCK_THRESHOLD = 0.72


def compute_fatigue(state: ChatSessionState, user_message: str = "") -> float:
    fatigue = state.fatigue_score
    fatigue += state.assessments_offered * 0.12
    fatigue += max(0, state.assessments_offered - state.assessments_completed) * 0.18
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


def should_block_new_assessment(state: ChatSessionState, user_message: str) -> bool:
    fatigue = compute_fatigue(state, user_message)
    state.fatigue_score = fatigue

    if state.turn_count < WARMUP_TURNS:
        return True
    if fatigue >= FATIGUE_BLOCK_THRESHOLD:
        return True
    if state.pending_assessment:
        return True
    if state.assessments_offered >= MAX_ASSESSMENTS_PER_SESSION:
        return True
    if state.assessments_offered > 0 and (state.turn_count - state.last_assessment_turn) < MIN_TURNS_BETWEEN_ASSESSMENTS:
        return True
    return False


def detect_distress(user_message: str) -> bool:
    normalized = (user_message or "").lower()
    return any(keyword in normalized for keyword in DISTRESS_KEYWORDS)


def detect_counseling_request(user_message: str) -> bool:
    normalized = (user_message or "").lower()
    return any(keyword in normalized for keyword in COUNSELING_REQUEST_KEYWORDS)
