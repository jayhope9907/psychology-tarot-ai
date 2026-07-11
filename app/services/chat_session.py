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
    clinical_insight: Dict[str, Any] = field(default_factory=dict)
    counseling_phase: str = "rapport"
    phase_history: List[str] = field(default_factory=list)
    phase_notes: Dict[str, Any] = field(default_factory=dict)
    assessment_package: Optional[Dict[str, Any]] = None
    assessment_package_ready: bool = False
    assessment_paid: bool = False
    payment_id: Optional[str] = None
    tarot_handoff: Optional[Dict[str, Any]] = None
    tarot_blended: bool = False
    homework_packages: List[Dict[str, Any]] = field(default_factory=list)
    homework_completed: List[Dict[str, Any]] = field(default_factory=list)
    pending_homework: Optional[Dict[str, Any]] = None
    org_id: Optional[str] = None
    org_name: Optional[str] = None
    org_entitlements: Optional[Dict[str, Any]] = None
    association_license_key: Optional[str] = None

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
            "clinical_insight": self.clinical_insight,
            "counseling_phase": self.counseling_phase,
            "phase_history": self.phase_history,
            "phase_notes": self.phase_notes,
            "assessment_package_ready": self.assessment_package_ready,
            "assessment_paid": self.assessment_paid,
            "payment_id": self.payment_id,
            "tarot_blended": self.tarot_blended,
            "has_tarot_handoff": bool(self.tarot_handoff),
            "homework_pending": bool(self.pending_homework),
            "homework_completed_count": len(self.homework_completed),
            "message_count": len(self.messages),
            "org_id": self.org_id,
            "org_name": self.org_name,
            "discipline_id": (self.org_entitlements or {}).get("discipline_id"),
        }


CHAT_SESSIONS: Dict[str, ChatSessionState] = {}


def get_or_create_session(user_id: str, session_id: Optional[str] = None, plan: str = "FREE") -> ChatSessionState:
    from app.services.persistence import load_latest_session_for_user, load_session, save_session

    if session_id:
        if session_id in CHAT_SESSIONS:
            session = CHAT_SESSIONS[session_id]
            if session.user_id != user_id:
                session = ChatSessionState(user_id=user_id, session_id=session_id, plan=plan)
                CHAT_SESSIONS[session_id] = session
                save_session(session)
            return session
        loaded = load_session(session_id)
        if loaded:
            if loaded.user_id != user_id:
                loaded.user_id = user_id
                save_session(loaded)
            return loaded

    latest = load_latest_session_for_user(user_id)
    if latest and not session_id:
        return latest

    session = ChatSessionState(user_id=user_id, plan=plan)
    if session_id:
        session.session_id = session_id
    CHAT_SESSIONS[session.session_id] = session
    save_session(session)
    return session


def get_session(session_id: str) -> Optional[ChatSessionState]:
    from app.services.persistence import load_session

    if session_id in CHAT_SESSIONS:
        return CHAT_SESSIONS[session_id]
    return load_session(session_id)


def clear_sessions() -> None:
    CHAT_SESSIONS.clear()
    try:
        from app.db.database import reset_db

        reset_db()
    except Exception:
        pass
