from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.db.database import get_connection, init_db
from app.services.chat_session import CHAT_SESSIONS, ChatSessionState


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_user(user_id: str, display_name: Optional[str] = None) -> None:
    init_db()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO users (user_id, display_name, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                display_name = COALESCE(excluded.display_name, users.display_name),
                updated_at = excluded.updated_at
            """,
            (user_id, display_name, _utc_now()),
        )
        conn.commit()
    finally:
        conn.close()


def session_to_storage(state: ChatSessionState) -> Dict[str, Any]:
    return {
        "user_id": state.user_id,
        "session_id": state.session_id,
        "turn_count": state.turn_count,
        "assessments_offered": state.assessments_offered,
        "assessments_completed": state.assessments_completed,
        "assessments_skipped": state.assessments_skipped,
        "last_assessment_turn": state.last_assessment_turn,
        "fatigue_score": state.fatigue_score,
        "messages": state.messages,
        "pending_assessment": state.pending_assessment,
        "formal_answers": state.formal_answers,
        "micro_answers": state.micro_answers,
        "plan": state.plan,
        "preferred_school": state.preferred_school,
        "persona_routing": state.persona_routing,
        "quant_features": state.quant_features,
        "battery_coverage": state.battery_coverage,
        "clinical_insight": state.clinical_insight,
        "counseling_phase": state.counseling_phase,
        "phase_history": state.phase_history,
        "phase_notes": state.phase_notes,
        "assessment_package": state.assessment_package,
        "assessment_package_ready": state.assessment_package_ready,
        "assessment_paid": state.assessment_paid,
        "payment_id": state.payment_id,
        "tarot_handoff": state.tarot_handoff,
        "tarot_blended": state.tarot_blended,
        "homework_packages": state.homework_packages,
        "homework_completed": state.homework_completed,
        "pending_homework": state.pending_homework,
        "org_id": state.org_id,
        "org_name": state.org_name,
        "org_entitlements": state.org_entitlements,
        "association_license_key": state.association_license_key,
    }


def session_from_storage(data: Dict[str, Any]) -> ChatSessionState:
    return ChatSessionState(
        user_id=data["user_id"],
        session_id=data["session_id"],
        turn_count=data.get("turn_count", 0),
        assessments_offered=data.get("assessments_offered", 0),
        assessments_completed=data.get("assessments_completed", 0),
        assessments_skipped=data.get("assessments_skipped", 0),
        last_assessment_turn=data.get("last_assessment_turn", -99),
        fatigue_score=data.get("fatigue_score", 0.0),
        messages=data.get("messages", []),
        pending_assessment=data.get("pending_assessment"),
        formal_answers=data.get("formal_answers", {}),
        micro_answers=data.get("micro_answers", []),
        plan=data.get("plan", "FREE"),
        preferred_school=data.get("preferred_school"),
        persona_routing=data.get("persona_routing"),
        quant_features=data.get("quant_features", {}),
        battery_coverage=data.get("battery_coverage", {}),
        clinical_insight=data.get("clinical_insight", {}),
        counseling_phase=data.get("counseling_phase", "rapport"),
        phase_history=data.get("phase_history", []),
        phase_notes=data.get("phase_notes", {}),
        assessment_package=data.get("assessment_package"),
        assessment_package_ready=data.get("assessment_package_ready", False),
        assessment_paid=data.get("assessment_paid", False),
        payment_id=data.get("payment_id"),
        tarot_handoff=data.get("tarot_handoff"),
        tarot_blended=data.get("tarot_blended", False),
        homework_packages=data.get("homework_packages", []),
        homework_completed=data.get("homework_completed", []),
        pending_homework=data.get("pending_homework"),
        org_id=data.get("org_id"),
        org_name=data.get("org_name"),
        org_entitlements=data.get("org_entitlements"),
        association_license_key=data.get("association_license_key"),
    )


def save_session(state: ChatSessionState) -> None:
    init_db()
    ensure_user(state.user_id)
    payload = json.dumps(session_to_storage(state), ensure_ascii=False)
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO session_snapshots (session_id, user_id, state_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                user_id = excluded.user_id,
                state_json = excluded.state_json,
                updated_at = excluded.updated_at
            """,
            (state.session_id, state.user_id, payload, _utc_now()),
        )
        conn.commit()
    finally:
        conn.close()
    CHAT_SESSIONS[state.session_id] = state


def load_session(session_id: str) -> Optional[ChatSessionState]:
    init_db()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT state_json FROM session_snapshots WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        data = json.loads(row["state_json"])
        state = session_from_storage(data)
        CHAT_SESSIONS[session_id] = state
        return state
    finally:
        conn.close()


def load_latest_session_for_user(user_id: str) -> Optional[ChatSessionState]:
    init_db()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT state_json FROM session_snapshots
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        if not row:
            return None
        data = json.loads(row["state_json"])
        state = session_from_storage(data)
        CHAT_SESSIONS[state.session_id] = state
        return state
    finally:
        conn.close()


def list_user_sessions(user_id: str, limit: int = 12) -> List[Dict[str, Any]]:
    init_db()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT session_id, state_json, updated_at
            FROM session_snapshots
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        sessions: List[Dict[str, Any]] = []
        for row in rows:
            data = json.loads(row["state_json"])
            messages = data.get("messages") or []
            preview = ""
            for entry in reversed(messages):
                if entry.get("role") == "user" and entry.get("content"):
                    preview = str(entry["content"])[:72]
                    break
            sessions.append(
                {
                    "session_id": row["session_id"],
                    "updated_at": row["updated_at"],
                    "turn_count": data.get("turn_count", 0),
                    "message_count": len(messages),
                    "counseling_phase": data.get("counseling_phase", "rapport"),
                    "preview": preview,
                }
            )
        return sessions
    finally:
        conn.close()


def record_tarot_draw(user_id: str, draw: Dict[str, Any]) -> int:
    init_db()
    ensure_user(user_id)
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO tarot_draws (user_id, spread, draw_json) VALUES (?, ?, ?)",
            (user_id, draw.get("spread", "three_card"), json.dumps(draw, ensure_ascii=False)),
        )
        conn.commit()
        return int(cur.lastrowid or 0)
    finally:
        conn.close()


def list_tarot_draws(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    init_db()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, spread, draw_json, created_at FROM tarot_draws
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        results = []
        for row in rows:
            draw = json.loads(row["draw_json"])
            results.append(
                {
                    "id": row["id"],
                    "spread": row["spread"],
                    "created_at": row["created_at"],
                    "cards": draw.get("cards", []),
                    "spread_label_ko": draw.get("spread_label_ko"),
                }
            )
        return results
    finally:
        conn.close()


def get_user_settings(user_id: str) -> Dict[str, Any]:
    init_db()
    ensure_user(user_id)
    conn = get_connection()
    try:
        row = conn.execute("SELECT settings_json FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            return {}
        return json.loads(row["settings_json"] or "{}")
    finally:
        conn.close()


def save_user_settings(user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    init_db()
    ensure_user(user_id)
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET settings_json = ?, updated_at = ? WHERE user_id = ?",
            (json.dumps(settings, ensure_ascii=False), _utc_now(), user_id),
        )
        conn.commit()
        return settings
    finally:
        conn.close()
