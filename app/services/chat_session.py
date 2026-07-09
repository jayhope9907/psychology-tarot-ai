from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class ChatSessionState:
    user_id: str
    session_id: str = field(default_factory=lambda: str(uuid4()))
    turn_count: int = 0
    assessments_offered: int = 0
    assessments_completed: int = 0
    assessments_skipped: int = 0
    last_assessment_turn: int = -99
    fatigue_score: float = 0.0
    messages: List[Dict[str, str]] = field(default_factory=list)
    pending_assessment: Optional[Dict[str, Any]] = None
    formal_answers: Dict[str, Dict[str, int]] = field(default_factory=dict)
    micro_answers: List[Dict[str, Any]] = field(default_factory=list)
    plan: str = "FREE"
    preferred_school: Optional[str] = None
    persona_routing: Optional[Dict[str, Any]] = None
    quant_features: Dict[str, Any] = field(default_factory=dict)
    battery_coverage: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "turn_count": self.turn_count,
            "assessments_offered": self.assessments_offered,
            "assessments_completed": self.assessments_completed,
            "assessments_skipped": self.assessments_skipped,
            "last_assessment_turn": self.last_assessment_turn,
            "fatigue_score": self.fatigue_score,
            "pending_assessment": self.pending_assessment,
            "formal_answers": self.formal_answers,
            "micro_answers": self.micro_answers,
            "plan": self.plan,
            "preferred_school": self.preferred_school,
            "persona_routing": self.persona_routing,
            "quant_features": self.quant_features,
            "battery_coverage": self.battery_coverage,
            "message_count": len(self.messages),
        }


CHAT_SESSIONS: Dict[str, ChatSessionState] = {}


def get_or_create_session(user_id: str, session_id: Optional[str] = None, plan: str = "FREE") -> ChatSessionState:
    if session_id and session_id in CHAT_SESSIONS:
        session = CHAT_SESSIONS[session_id]
        if session.user_id != user_id:
            session = ChatSessionState(user_id=user_id, session_id=session_id, plan=plan)
            CHAT_SESSIONS[session_id] = session
        return session

    session = ChatSessionState(user_id=user_id, plan=plan)
    CHAT_SESSIONS[session.session_id] = session
    return session


def clear_sessions() -> None:
    CHAT_SESSIONS.clear()
