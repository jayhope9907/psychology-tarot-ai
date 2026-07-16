"""Persist stress management interventions for patent / B2B audit."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

from app.db.database import get_connection, init_db
from app.services.persistence import ensure_user, get_user_settings, save_user_settings
from app.services.stress_management import build_stress_management_plan

HISTORY_RING_MAX = 40
SETTINGS_KEY = "lastStressManagement"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_stress_tables() -> None:
    init_db()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def persist_stress_management_tick(
    *,
    user_id: str,
    session_id: str = "",
    user_message: str = "",
    turn_index: int = 0,
    source: str = "chat",
    clinical_setup: Optional[Mapping[str, Any]] = None,
    pre_sud: Optional[float] = None,
    post_sud: Optional[float] = None,
    intervention_effectiveness: Optional[float] = None,
    license_type: str = "B2C_personal",
    organization_id: Optional[str] = None,
    state: Any = None,
) -> Dict[str, Any]:
    ensure_stress_tables()
    ensure_user(user_id)

    plan = build_stress_management_plan(clinical_setup=_as_dict(clinical_setup), pre_sud=pre_sud)
    org = organization_id or None
    when = _utc_now()
    sid = session_id or ""
    turn = max(0, int(turn_index or 0))
    src = (source or "chat").strip()[:32] or "chat"
    cue = (user_message or "").strip()[:120]

    record = {
        "userId": user_id,
        "sessionId": sid,
        "turnIndex": turn,
        "source": src,
        "protocolId": plan["protocolId"],
        "protocolVersion": plan["protocolVersion"],
        "userMessageCue": cue,
        "plan": plan,
        "preSud": pre_sud,
        "postSud": post_sud,
        "interventionEffectiveness": intervention_effectiveness,
        "clinicalAdaptiveSetup": plan.get("clinicalAdaptiveSetup"),
        "licenseType": license_type or "B2C_personal",
        "organizationId": org,
        "recordedAt": when,
        "non_diagnostic": True,
    }

    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO stress_management_history (
                user_id, session_id, turn_index, source,
                protocol_id, protocol_version, user_message_cue,
                plan_json, pre_sud, post_sud, intervention_effectiveness,
                clinical_setup_json, license_type, organization_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                sid,
                turn,
                src,
                plan["protocolId"],
                plan["protocolVersion"],
                cue,
                json.dumps(plan, ensure_ascii=False),
                pre_sud,
                post_sud,
                intervention_effectiveness,
                json.dumps(plan.get("clinicalAdaptiveSetup") or {}, ensure_ascii=False),
                license_type or "B2C_personal",
                org,
                when,
            ),
        )
        record["id"] = int(cur.lastrowid or 0)

        conn.execute(
            """
            UPDATE users
            SET last_stress_json = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (json.dumps(record, ensure_ascii=False), when, user_id),
        )
        conn.commit()
    finally:
        conn.close()

    try:
        settings = get_user_settings(user_id)
        settings[SETTINGS_KEY] = {
            "plan": plan,
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
            notes["stress_management"] = record
            ring = list(notes.get("stress_management_history") or [])
            ring.append(
                {
                    "id": record.get("id"),
                    "turnIndex": turn,
                    "protocolId": plan["protocolId"],
                    "recordedAt": when,
                    "preSud": pre_sud,
                    "postSud": post_sud,
                }
            )
            notes["stress_management_history"] = ring[-HISTORY_RING_MAX:]
        except Exception:
            pass

    try:
        from app.services.psych_timeline import record_event

        record_event(
            user_id,
            "stress_management_tick",
            {
                "session_id": sid,
                "turn_index": turn,
                "source": src,
                "protocolId": plan["protocolId"],
                "preSud": pre_sud,
                "postSud": post_sud,
                "interventionEffectiveness": intervention_effectiveness,
                "licenseType": license_type,
                "organizationId": org,
                "non_diagnostic": True,
            },
            source_id=f"smh:{sid or 'user'}:{src}:{turn}:{record.get('id')}",
            event_at=when,
        )
    except Exception:
        pass

    return record


def list_stress_history(
    user_id: str,
    *,
    session_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    ensure_stress_tables()
    lim = max(1, min(int(limit or 50), 200))
    conn = get_connection()
    try:
        if session_id:
            rows = conn.execute(
                """
                SELECT id, user_id, session_id, turn_index, source,
                       protocol_id, protocol_version, user_message_cue,
                       plan_json, pre_sud, post_sud, intervention_effectiveness,
                       clinical_setup_json, license_type, organization_id, created_at
                FROM stress_management_history
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
                       protocol_id, protocol_version, user_message_cue,
                       plan_json, pre_sud, post_sud, intervention_effectiveness,
                       clinical_setup_json, license_type, organization_id, created_at
                FROM stress_management_history
                WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (user_id, lim),
            ).fetchall()
        return [_row_to_public(r) for r in rows]
    finally:
        conn.close()


def list_org_stress_history(organization_id: str, *, limit: int = 100) -> List[Dict[str, Any]]:
    ensure_stress_tables()
    lim = max(1, min(int(limit or 100), 500))
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, user_id, session_id, turn_index, source,
                   protocol_id, protocol_version, user_message_cue,
                   plan_json, pre_sud, post_sud, intervention_effectiveness,
                   clinical_setup_json, license_type, organization_id, created_at
            FROM stress_management_history
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


def get_user_last_stress(user_id: str) -> Optional[Dict[str, Any]]:
    ensure_stress_tables()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT last_stress_json, updated_at FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row or not row["last_stress_json"]:
            return None
        payload = json.loads(row["last_stress_json"] or "{}")
        payload["updatedAt"] = row["updated_at"]
        return payload
    finally:
        conn.close()


def session_stress_summary(session_id: str) -> Dict[str, Any]:
    ensure_stress_tables()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT turn_index, protocol_id, pre_sud, post_sud, source, created_at
            FROM stress_management_history
            WHERE session_id = ?
            ORDER BY turn_index ASC, id ASC
            """,
            (session_id,),
        ).fetchall()
        return {
            "sessionId": session_id,
            "tickCount": len(rows),
            "turnIndices": [int(r["turn_index"]) for r in rows],
            "protocols": sorted({str(r["protocol_id"]) for r in rows}),
            "precise": len(rows) > 0 and len({int(r["turn_index"]) for r in rows}) == len(rows),
            "latest": (
                {
                    "turnIndex": int(rows[-1]["turn_index"]),
                    "protocolId": rows[-1]["protocol_id"],
                    "preSud": rows[-1]["pre_sud"],
                    "postSud": rows[-1]["post_sud"],
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
        "protocolId": row["protocol_id"],
        "protocolVersion": row["protocol_version"],
        "userMessageCue": row["user_message_cue"],
        "plan": json.loads(row["plan_json"] or "{}"),
        "preSud": row["pre_sud"],
        "postSud": row["post_sud"],
        "interventionEffectiveness": row["intervention_effectiveness"],
        "clinicalAdaptiveSetup": json.loads(row["clinical_setup_json"] or "{}"),
        "licenseType": row["license_type"],
        "organizationId": row["organization_id"],
        "createdAt": row["created_at"],
        "non_diagnostic": True,
    }


def _hash_user(user_id: str) -> str:
    return hashlib.sha256(f"smh:{user_id}".encode("utf-8")).hexdigest()[:16]
