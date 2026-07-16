"""DB persistence for sanitized_input history + migration build checks."""
from __future__ import annotations

from app.db.database import get_connection, init_db
from app.services.chat_session import ChatSessionState
from app.services.input_sanitizer import sanitize_and_compensate
from app.services.persistence import get_user_settings, load_session, save_session
from app.services.sanitized_input_store import (
    get_user_last_sanitized,
    list_sanitized_history,
    persist_sanitized_input,
    session_tracking_summary,
)


def test_schema_has_sanitized_history_and_user_columns():
    init_db(force=True)
    conn = get_connection()
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "sanitized_input_history" in tables
        user_cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
        assert "last_sanitized_json" in user_cols
        assert "consultation_mode" in user_cols
        sess_cols = {r[1] for r in conn.execute("PRAGMA table_info(session_snapshots)")}
        assert "last_sanitized_json" in sess_cols
        assert "current_step" in sess_cols
        assert "consultation_mode" in sess_cols
    finally:
        conn.close()


def test_persist_accumulates_turn_precise_history():
    state = ChatSessionState(user_id="sih-user", session_id="sih-sess")
    state.consultation_mode = "psychology"
    state.license_type = "B2B_society_general"
    state.organization_id = "org-demo"
    save_session(state)

    for turn in (1, 2, 3):
        snap = sanitize_and_compensate(
            {
                "consultationMode": "psychology" if turn < 3 else "faith",
                "step": turn,
                "selectedCard": "The Moon" if turn >= 2 else None,
                "checkInMetrics": {"mood": 40 + turn * 5} if turn > 1 else None,
            }
        )
        persist_sanitized_input(
            user_id=state.user_id,
            session_id=state.session_id,
            sanitized=snap,
            turn_index=turn,
            source="chat",
            psychodynamic_metrics={"persona_fatigue": 50 + turn, "defense_mechanism": "억압"},
            license_type=state.license_type,
            organization_id=state.organization_id,
            state=state,
        )

    save_session(state)
    history = list_sanitized_history(state.user_id, session_id=state.session_id, limit=20)
    assert len(history) == 3
    assert [h["turnIndex"] for h in history] == [1, 2, 3]
    assert history[0]["dominantArchetype"] == "None"
    assert history[1]["dominantArchetype"] == "The Moon"
    assert history[2]["isFaithMode"] is True
    assert history[2]["defenseMechanismEnabled"] is False

    summary = session_tracking_summary(state.session_id)
    assert summary["tickCount"] == 3
    assert summary["precise"] is True
    assert summary["stepsCovered"] == [1, 2, 3]
    assert "faith" in summary["modesCovered"]

    latest = get_user_last_sanitized(state.user_id)
    assert latest is not None
    assert latest["sanitizedInput"]["isFaithMode"] is True

    settings = get_user_settings(state.user_id)
    assert settings.get("lastSanitizedInput", {}).get("turnIndex") == 3

    reloaded = load_session(state.session_id)
    assert reloaded is not None
    assert reloaded.phase_notes.get("sanitized_input", {}).get("isFaithMode") is True
    assert len(reloaded.phase_notes.get("sanitized_input_history") or []) == 3

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT consultation_mode, current_step, last_sanitized_json FROM session_snapshots WHERE session_id = ?",
            (state.session_id,),
        ).fetchone()
        assert row["consultation_mode"] == "faith"
        assert int(row["current_step"]) == 3
        assert "The Moon" in (row["last_sanitized_json"] or "")
    finally:
        conn.close()
