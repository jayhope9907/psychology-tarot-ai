"""Persist sanitizeAndCompensate outputs for patent / B2B session tracking.

Writes:
  1) append-only `sanitized_input_history` (turn-precise)
  2) `users.last_sanitized_json` + settings mirror
  3) session `phase_notes` ring buffer + denormalized session columns
  4) psych_timeline event (`sanitized_input_tick`)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

from app.db.database import get_connection, init_db
from app.services.persistence import ensure_user, get_user_settings, save_user_settings

HISTORY_RING_MAX = 40
SETTINGS_KEY = "lastSanitizedInput"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_sanitized_tables() -> None:
    init_db()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def persist_sanitized_input(
    *,
    user_id: str,
    session_id: str = "",
    sanitized: Mapping[str, Any],
    turn_index: int = 0,
    source: str = "chat",
    psychodynamic_metrics: Optional[Mapping[str, Any]] = None,
    license_type: str = "B2C_personal",
    organization_id: Optional[str] = None,
    state: Any = None,
) -> Dict[str, Any]:
    """Store one compensated input tick and sync user + optional session state."""
    ensure_sanitized_tables()
    ensure_user(user_id)

    snap = _as_dict(sanitized)
    mode = str(snap.get("consultationMode") or snap.get("mode") or "psychology")
    step = int(snap.get("currentStep") or snap.get("step") or 1)
    archetype = str(snap.get("dominantArchetype") or "None")
    weights = _as_dict(snap.get("initialWeights") or snap.get("checkInMetrics"))
    is_faith = bool(snap.get("isFaithMode") or mode == "faith")
    defense_on = bool(snap.get("defenseMechanismEnabled", not is_faith))
    metrics = _as_dict(psychodynamic_metrics)
    org = organization_id or None
    when = _utc_now()
    sid = session_id or ""
    turn = max(0, int(turn_index or 0))
    src = (source or "chat").strip()[:32] or "chat"

    record = {
        "userId": user_id,
        "sessionId": sid,
        "turnIndex": turn,
        "source": src,
        "consultationMode": mode,
        "currentStep": step,
        "dominantArchetype": archetype,
        "initialWeights": weights,
        "isFaithMode": is_faith,
        "defenseMechanismEnabled": defense_on,
        "psychodynamicMetrics": metrics or None,
        "licenseType": license_type or "B2C_personal",
        "organizationId": org,
        "sanitizedInput": snap,
        "recordedAt": when,
        "non_diagnostic": True,
    }

    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO sanitized_input_history (
                user_id, session_id, turn_index, source,
                consultation_mode, current_step, dominant_archetype,
                initial_weights_json, defense_mechanism_enabled, is_faith_mode,
                sanitized_json, psychodynamic_json,
                license_type, organization_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                sid,
                turn,
                src,
                mode,
                step,
                archetype,
                json.dumps(weights, ensure_ascii=False),
                1 if defense_on else 0,
                1 if is_faith else 0,
                json.dumps(snap, ensure_ascii=False),
                json.dumps(metrics, ensure_ascii=False),
                license_type or "B2C_personal",
                org,
                when,
            ),
        )
        record["id"] = int(cur.lastrowid or 0)

        conn.execute(
            """
            UPDATE users
            SET last_sanitized_json = ?, consultation_mode = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (json.dumps(snap, ensure_ascii=False), mode, when, user_id),
        )

        if sid:
            conn.execute(
                """
                UPDATE session_snapshots
                SET consultation_mode = ?,
                    current_step = ?,
                    last_sanitized_json = ?,
                    updated_at = ?
                WHERE session_id = ?
                """,
                (mode, step, json.dumps(snap, ensure_ascii=False), when, sid),
            )
        conn.commit()
    finally:
        conn.close()

    # Mirror into settings_json for product / B2B export compatibility
    try:
        settings = get_user_settings(user_id)
        settings[SETTINGS_KEY] = {
            "sanitizedInput": snap,
            "recordedAt": when,
            "sessionId": sid,
            "turnIndex": turn,
            "source": src,
        }
        settings["consultationMode"] = mode
        settings["consultation_mode"] = mode
        save_user_settings(user_id, settings)
    except Exception:
        pass

    # In-session ring buffer (also lands in session_snapshots.state_json via save_session)
    if state is not None:
        try:
            notes = getattr(state, "phase_notes", None)
            if notes is None:
                state.phase_notes = {}
                notes = state.phase_notes
            notes["sanitized_input"] = snap
            ring = list(notes.get("sanitized_input_history") or [])
            ring.append(
                {
                    "id": record.get("id"),
                    "turnIndex": turn,
                    "source": src,
                    "recordedAt": when,
                    "consultationMode": mode,
                    "currentStep": step,
                    "dominantArchetype": archetype,
                    "initialWeights": weights,
                    "defenseMechanismEnabled": defense_on,
                    "isFaithMode": is_faith,
                }
            )
            notes["sanitized_input_history"] = ring[-HISTORY_RING_MAX:]
            if hasattr(state, "consultation_mode"):
                state.consultation_mode = mode
        except Exception:
            pass

    try:
        from app.services.psych_timeline import record_event

        record_event(
            user_id,
            "sanitized_input_tick",
            {
                "session_id": sid,
                "turn_index": turn,
                "source": src,
                "consultationMode": mode,
                "currentStep": step,
                "dominantArchetype": archetype,
                "initialWeights": weights,
                "defenseMechanismEnabled": defense_on,
                "isFaithMode": is_faith,
                "licenseType": license_type,
                "organizationId": org,
                "non_diagnostic": True,
            },
            source_id=f"sih:{sid or 'user'}:{src}:{turn}:{record.get('id')}",
            event_at=when,
        )
    except Exception:
        pass

    return record


def list_sanitized_history(
    user_id: str,
    *,
    session_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    ensure_sanitized_tables()
    lim = max(1, min(int(limit or 50), 200))
    conn = get_connection()
    try:
        if session_id:
            rows = conn.execute(
                """
                SELECT id, user_id, session_id, turn_index, source,
                       consultation_mode, current_step, dominant_archetype,
                       initial_weights_json, defense_mechanism_enabled, is_faith_mode,
                       sanitized_json, psychodynamic_json,
                       license_type, organization_id, created_at
                FROM sanitized_input_history
                WHERE user_id = ? AND session_id = ?
                ORDER BY turn_index ASC, id ASC
                LIMIT ?
                """,
                (user_id, session_id, lim),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, user_id, session_id, turn_index, source,
                       consultation_mode, current_step, dominant_archetype,
                       initial_weights_json, defense_mechanism_enabled, is_faith_mode,
                       sanitized_json, psychodynamic_json,
                       license_type, organization_id, created_at
                FROM sanitized_input_history
                WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (user_id, lim),
            ).fetchall()
        return [_row_to_public(r) for r in rows]
    finally:
        conn.close()


def list_org_sanitized_history(
    organization_id: str,
    *,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """B2B society dashboard: org-scoped ticks without raw free text."""
    ensure_sanitized_tables()
    lim = max(1, min(int(limit or 100), 500))
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, user_id, session_id, turn_index, source,
                   consultation_mode, current_step, dominant_archetype,
                   initial_weights_json, defense_mechanism_enabled, is_faith_mode,
                   sanitized_json, psychodynamic_json,
                   license_type, organization_id, created_at
            FROM sanitized_input_history
            WHERE organization_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (organization_id, lim),
        ).fetchall()
        out = []
        for row in rows:
            item = _row_to_public(row)
            # Hash user id for society dashboards
            uid = item.get("userId") or ""
            item["userIdHash"] = _hash_user(uid)
            item.pop("userId", None)
            out.append(item)
        return out
    finally:
        conn.close()


def get_user_last_sanitized(user_id: str) -> Optional[Dict[str, Any]]:
    ensure_sanitized_tables()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT last_sanitized_json, consultation_mode, updated_at FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row or not row["last_sanitized_json"]:
            return None
        return {
            "sanitizedInput": json.loads(row["last_sanitized_json"] or "{}"),
            "consultationMode": row["consultation_mode"],
            "updatedAt": row["updated_at"],
        }
    finally:
        conn.close()


def session_tracking_summary(session_id: str) -> Dict[str, Any]:
    """Precision check helper: history length + step/mode coverage for a session."""
    ensure_sanitized_tables()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT turn_index, consultation_mode, current_step, dominant_archetype,
                   is_faith_mode, defense_mechanism_enabled, source, created_at
            FROM sanitized_input_history
            WHERE session_id = ?
            ORDER BY turn_index ASC, id ASC
            """,
            (session_id,),
        ).fetchall()
        steps = sorted({int(r["current_step"]) for r in rows})
        modes = sorted({str(r["consultation_mode"]) for r in rows})
        return {
            "sessionId": session_id,
            "tickCount": len(rows),
            "turnIndices": [int(r["turn_index"]) for r in rows],
            "stepsCovered": steps,
            "modesCovered": modes,
            "sources": sorted({str(r["source"]) for r in rows}),
            "precise": len(rows) > 0 and len({int(r["turn_index"]) for r in rows}) == len(rows),
            "latest": (
                {
                    "turnIndex": int(rows[-1]["turn_index"]),
                    "currentStep": int(rows[-1]["current_step"]),
                    "consultationMode": rows[-1]["consultation_mode"],
                    "dominantArchetype": rows[-1]["dominant_archetype"],
                    "isFaithMode": bool(rows[-1]["is_faith_mode"]),
                    "defenseMechanismEnabled": bool(rows[-1]["defense_mechanism_enabled"]),
                    "source": rows[-1]["source"],
                    "createdAt": rows[-1]["created_at"],
                }
                if rows
                else None
            ),
        }
    finally:
        conn.close()


def _row_to_public(row: Any) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "userId": row["user_id"],
        "sessionId": row["session_id"],
        "turnIndex": row["turn_index"],
        "source": row["source"],
        "consultationMode": row["consultation_mode"],
        "currentStep": row["current_step"],
        "dominantArchetype": row["dominant_archetype"],
        "initialWeights": json.loads(row["initial_weights_json"] or "{}"),
        "defenseMechanismEnabled": bool(row["defense_mechanism_enabled"]),
        "isFaithMode": bool(row["is_faith_mode"]),
        "sanitizedInput": json.loads(row["sanitized_json"] or "{}"),
        "psychodynamicMetrics": json.loads(row["psychodynamic_json"] or "{}") or None,
        "licenseType": row["license_type"],
        "organizationId": row["organization_id"],
        "createdAt": row["created_at"],
        "non_diagnostic": True,
    }


def _hash_user(user_id: str) -> str:
    import hashlib

    return hashlib.sha256(f"sih:{user_id}".encode("utf-8")).hexdigest()[:16]
