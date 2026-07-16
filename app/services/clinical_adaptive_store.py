"""Persist Adaptive Clinical Setup ticks for patent / B2B audit."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

from app.db.database import get_connection, init_db
from app.services.clinical_adaptor import normalize_clinical_setup
from app.services.persistence import ensure_user, get_user_settings, save_user_settings

HISTORY_RING_MAX = 40
SETTINGS_KEY = "lastClinicalAdaptive"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_clinical_adaptive_tables() -> None:
    init_db()


def persist_clinical_adaptive_tick(
    *,
    user_id: str,
    session_id: str = "",
    turn_index: int = 0,
    source: str = "chat",
    resistance_level: Any = None,
    sensory_impairment_deaf: Any = None,
    cognitive_level: Any = None,
    license_type: str = "B2C_personal",
    organization_id: Optional[str] = None,
    state: Any = None,
) -> Dict[str, Any]:
    ensure_clinical_adaptive_tables()
    ensure_user(user_id)

    setup = normalize_clinical_setup(
        resistance_level=resistance_level,
        sensory_impairment_deaf=sensory_impairment_deaf,
        cognitive_level=cognitive_level,
    )
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
        "clinicalAdaptiveSetup": setup,
        "licenseType": license_type or "B2C_personal",
        "organizationId": org,
        "recordedAt": when,
        "non_diagnostic": True,
    }

    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO clinical_adaptive_history (
                user_id, session_id, turn_index, source,
                resistance_level, sensory_impairment_deaf, cognitive_level,
                adaptive_enabled, setup_json,
                license_type, organization_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                sid,
                turn,
                src,
                setup["resistance_level"],
                1 if setup["sensory_impairment_deaf"] else 0,
                setup["cognitive_level"],
                1 if setup["adaptive_enabled"] else 0,
                json.dumps(setup, ensure_ascii=False),
                license_type or "B2C_personal",
                org,
                when,
            ),
        )
        record["id"] = int(cur.lastrowid or 0)

        conn.execute(
            """
            UPDATE users
            SET last_clinical_adaptive_json = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (json.dumps(setup, ensure_ascii=False), when, user_id),
        )

        if sid:
            conn.execute(
                """
                UPDATE session_snapshots
                SET resistance_level = ?,
                    sensory_impairment_deaf = ?,
                    cognitive_level = ?,
                    updated_at = ?
                WHERE session_id = ?
                """,
                (
                    setup["resistance_level"],
                    1 if setup["sensory_impairment_deaf"] else 0,
                    setup["cognitive_level"],
                    when,
                    sid,
                ),
            )
        conn.commit()
    finally:
        conn.close()

    try:
        settings = get_user_settings(user_id)
        settings[SETTINGS_KEY] = {
            "clinicalAdaptiveSetup": setup,
            "recordedAt": when,
            "sessionId": sid,
            "turnIndex": turn,
            "source": src,
        }
        save_user_settings(user_id, settings)
    except Exception:
        pass

    if state is not None:
        try:
            notes = getattr(state, "phase_notes", None)
            if notes is None:
                state.phase_notes = {}
                notes = state.phase_notes
            notes["clinical_adaptive_setup"] = setup
            ring = list(notes.get("clinical_adaptive_history") or [])
            ring.append(
                {
                    "id": record.get("id"),
                    "turnIndex": turn,
                    "resistanceLevel": setup["resistance_level"],
                    "sensoryImpairmentDeaf": setup["sensory_impairment_deaf"],
                    "cognitiveLevel": setup["cognitive_level"],
                    "adaptiveEnabled": setup["adaptive_enabled"],
                    "recordedAt": when,
                }
            )
            notes["clinical_adaptive_history"] = ring[-HISTORY_RING_MAX:]
            if hasattr(state, "resistance_level"):
                state.resistance_level = setup["resistance_level"]
            if hasattr(state, "sensory_impairment_deaf"):
                state.sensory_impairment_deaf = setup["sensory_impairment_deaf"]
            if hasattr(state, "cognitive_level"):
                state.cognitive_level = setup["cognitive_level"]
        except Exception:
            pass

    try:
        from app.services.psych_timeline import record_event

        record_event(
            user_id,
            "clinical_adaptive_tick",
            {
                "session_id": sid,
                "turn_index": turn,
                "source": src,
                "resistanceLevel": setup["resistance_level"],
                "sensoryImpairmentDeaf": setup["sensory_impairment_deaf"],
                "cognitiveLevel": setup["cognitive_level"],
                "adaptiveEnabled": setup["adaptive_enabled"],
                "licenseType": license_type,
                "organizationId": org,
                "non_diagnostic": True,
            },
            source_id=f"cah:{sid or 'user'}:{src}:{turn}:{record.get('id')}",
            event_at=when,
        )
    except Exception:
        pass

    return record


def list_clinical_adaptive_history(
    user_id: str,
    *,
    session_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    ensure_clinical_adaptive_tables()
    lim = max(1, min(int(limit or 50), 200))
    conn = get_connection()
    try:
        if session_id:
            rows = conn.execute(
                """
                SELECT id, user_id, session_id, turn_index, source,
                       resistance_level, sensory_impairment_deaf, cognitive_level,
                       adaptive_enabled, setup_json,
                       license_type, organization_id, created_at
                FROM clinical_adaptive_history
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
                       resistance_level, sensory_impairment_deaf, cognitive_level,
                       adaptive_enabled, setup_json,
                       license_type, organization_id, created_at
                FROM clinical_adaptive_history
                WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (user_id, lim),
            ).fetchall()
        return [_row_to_public(r) for r in rows]
    finally:
        conn.close()


def list_org_clinical_adaptive_history(organization_id: str, *, limit: int = 100) -> List[Dict[str, Any]]:
    ensure_clinical_adaptive_tables()
    lim = max(1, min(int(limit or 100), 500))
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, user_id, session_id, turn_index, source,
                   resistance_level, sensory_impairment_deaf, cognitive_level,
                   adaptive_enabled, setup_json,
                   license_type, organization_id, created_at
            FROM clinical_adaptive_history
            WHERE organization_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (organization_id, lim),
        ).fetchall()
        out = []
        for row in rows:
            item = _row_to_public(row)
            uid = item.pop("userId", "")
            item["userIdHash"] = _hash_user(uid)
            out.append(item)
        return out
    finally:
        conn.close()


def get_user_last_clinical_adaptive(user_id: str) -> Optional[Dict[str, Any]]:
    ensure_clinical_adaptive_tables()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT last_clinical_adaptive_json, updated_at FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row or not row["last_clinical_adaptive_json"]:
            return None
        return {
            "clinicalAdaptiveSetup": json.loads(row["last_clinical_adaptive_json"] or "{}"),
            "updatedAt": row["updated_at"],
        }
    finally:
        conn.close()


def session_clinical_adaptive_summary(session_id: str) -> Dict[str, Any]:
    ensure_clinical_adaptive_tables()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT turn_index, resistance_level, cognitive_level,
                   sensory_impairment_deaf, adaptive_enabled, source, created_at
            FROM clinical_adaptive_history
            WHERE session_id = ?
            ORDER BY turn_index ASC, id ASC
            """,
            (session_id,),
        ).fetchall()
        return {
            "sessionId": session_id,
            "tickCount": len(rows),
            "turnIndices": [int(r["turn_index"]) for r in rows],
            "adaptiveEnabledCount": sum(1 for r in rows if r["adaptive_enabled"]),
            "precise": len(rows) > 0 and len({int(r["turn_index"]) for r in rows}) == len(rows),
            "latest": (
                {
                    "turnIndex": int(rows[-1]["turn_index"]),
                    "resistanceLevel": rows[-1]["resistance_level"],
                    "cognitiveLevel": rows[-1]["cognitive_level"],
                    "sensoryImpairmentDeaf": bool(rows[-1]["sensory_impairment_deaf"]),
                    "adaptiveEnabled": bool(rows[-1]["adaptive_enabled"]),
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
        "resistanceLevel": row["resistance_level"],
        "sensoryImpairmentDeaf": bool(row["sensory_impairment_deaf"]),
        "cognitiveLevel": row["cognitive_level"],
        "adaptiveEnabled": bool(row["adaptive_enabled"]),
        "clinicalAdaptiveSetup": json.loads(row["setup_json"] or "{}"),
        "licenseType": row["license_type"],
        "organizationId": row["organization_id"],
        "createdAt": row["created_at"],
        "non_diagnostic": True,
    }


def _hash_user(user_id: str) -> str:
    return hashlib.sha256(f"cah:{user_id}".encode("utf-8")).hexdigest()[:16]
