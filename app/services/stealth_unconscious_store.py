"""Persist 11-prop stealth unconscious assessments for patent / B2B audit."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

from app.db.database import get_connection, init_db
from app.services.persistence import ensure_user, get_user_settings, save_user_settings

HISTORY_RING_MAX = 40
SETTINGS_KEY = "lastStealthUnconscious"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_stealth_tables() -> None:
    init_db()


def persist_stealth_assessment(
    *,
    user_id: str,
    session_id: str = "",
    turn_index: int = 0,
    source: str = "prop_game",
    result: Mapping[str, Any],
    license_type: str = "B2C_personal",
    organization_id: Optional[str] = None,
    state: Any = None,
) -> Dict[str, Any]:
    ensure_stealth_tables()
    ensure_user(user_id)

    doc = dict(result or {})
    chc = dict(doc.get("chcProfile") or {})
    clinical = dict(doc.get("clinicalProfile") or {})
    stats = dict(doc.get("stats") or {})
    progress = dict(doc.get("progress") or {})
    completion = float(progress.get("completionRatio") or 0.0)
    persona = str(doc.get("persona") or "")
    persona_title = str(doc.get("title") or "")
    org = organization_id or None
    when = _utc_now()
    sid = session_id or ""
    turn = max(0, int(turn_index or 0))
    src = (source or "prop_game").strip()[:32] or "prop_game"

    record = {
        "userId": user_id,
        "sessionId": sid,
        "turnIndex": turn,
        "source": src,
        "persona": persona,
        "title": persona_title,
        "awakeningQuote": doc.get("awakeningQuote") or "",
        "completionRatio": completion,
        "chcProfile": chc,
        "clinicalProfile": clinical,
        "stats": stats,
        "result": doc,
        "licenseType": license_type or "B2C_personal",
        "organizationId": org,
        "recordedAt": when,
        "non_diagnostic": True,
    }

    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO stealth_unconscious_history (
                user_id, session_id, turn_index, source,
                persona, persona_title, completion_ratio,
                chc_json, clinical_json, stats_json, result_json,
                license_type, organization_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                sid,
                turn,
                src,
                persona,
                persona_title,
                completion,
                json.dumps(chc, ensure_ascii=False),
                json.dumps(clinical, ensure_ascii=False),
                json.dumps(stats, ensure_ascii=False),
                json.dumps(doc, ensure_ascii=False),
                license_type or "B2C_personal",
                org,
                when,
            ),
        )
        record["id"] = int(cur.lastrowid or 0)

        conn.execute(
            """
            UPDATE users
            SET last_stealth_unconscious_json = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (json.dumps(doc, ensure_ascii=False), when, user_id),
        )
        conn.commit()
    finally:
        conn.close()

    try:
        settings = get_user_settings(user_id)
        settings[SETTINGS_KEY] = {
            "persona": persona,
            "title": persona_title,
            "completionRatio": completion,
            "recordedAt": when,
            "sessionId": sid,
            "turnIndex": turn,
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
            notes["stealth_unconscious"] = doc
            ring = list(notes.get("stealth_unconscious_history") or [])
            ring.append(
                {
                    "id": record.get("id"),
                    "turnIndex": turn,
                    "persona": persona,
                    "completionRatio": completion,
                    "recordedAt": when,
                }
            )
            notes["stealth_unconscious_history"] = ring[-HISTORY_RING_MAX:]
        except Exception:
            pass

    try:
        from app.services.psych_timeline import record_event

        record_event(
            user_id,
            "stealth_unconscious_assessment",
            {
                "session_id": sid,
                "turn_index": turn,
                "source": src,
                "persona": persona,
                "completionRatio": completion,
                "licenseType": license_type,
                "organizationId": org,
                "non_diagnostic": True,
            },
            source_id=f"suh:{sid or 'user'}:{src}:{turn}:{record.get('id')}",
            event_at=when,
        )
    except Exception:
        pass

    return record


def list_stealth_history(
    user_id: str,
    *,
    session_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    ensure_stealth_tables()
    lim = max(1, min(int(limit or 50), 200))
    conn = get_connection()
    try:
        if session_id:
            rows = conn.execute(
                """
                SELECT id, user_id, session_id, turn_index, source,
                       persona, persona_title, completion_ratio,
                       chc_json, clinical_json, stats_json, result_json,
                       license_type, organization_id, created_at
                FROM stealth_unconscious_history
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
                       persona, persona_title, completion_ratio,
                       chc_json, clinical_json, stats_json, result_json,
                       license_type, organization_id, created_at
                FROM stealth_unconscious_history
                WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (user_id, lim),
            ).fetchall()
        return [_row_to_public(r) for r in rows]
    finally:
        conn.close()


def list_org_stealth_history(organization_id: str, *, limit: int = 100) -> List[Dict[str, Any]]:
    ensure_stealth_tables()
    lim = max(1, min(int(limit or 100), 500))
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, user_id, session_id, turn_index, source,
                   persona, persona_title, completion_ratio,
                   chc_json, clinical_json, stats_json, result_json,
                   license_type, organization_id, created_at
            FROM stealth_unconscious_history
            WHERE organization_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (organization_id, lim),
        ).fetchall()
        out: List[Dict[str, Any]] = []
        for row in rows:
            item = _row_to_public(row)
            uid = item.pop("userId", "")
            item["userIdHash"] = _hash_user(uid)
            out.append(item)
        return out
    finally:
        conn.close()


def get_user_last_stealth(user_id: str) -> Optional[Dict[str, Any]]:
    ensure_stealth_tables()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT last_stealth_unconscious_json, updated_at FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row or not row["last_stealth_unconscious_json"]:
            return None
        try:
            doc = json.loads(row["last_stealth_unconscious_json"] or "{}")
        except (TypeError, ValueError):
            return None
        if not doc:
            return None
        doc["updatedAt"] = row["updated_at"]
        return doc
    finally:
        conn.close()


def _json_field(row: Any, key: str) -> Dict[str, Any]:
    keys = set(row.keys()) if hasattr(row, "keys") else set()
    if key not in keys or not row[key]:
        return {}
    try:
        return json.loads(row[key] or "{}")
    except (TypeError, ValueError):
        return {}


def _row_to_public(row: Any) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "userId": row["user_id"],
        "sessionId": row["session_id"],
        "turnIndex": row["turn_index"],
        "source": row["source"],
        "persona": row["persona"],
        "title": row["persona_title"],
        "completionRatio": row["completion_ratio"],
        "chcProfile": _json_field(row, "chc_json"),
        "clinicalProfile": _json_field(row, "clinical_json"),
        "stats": _json_field(row, "stats_json"),
        "result": _json_field(row, "result_json"),
        "licenseType": row["license_type"],
        "organizationId": row["organization_id"],
        "createdAt": row["created_at"],
        "non_diagnostic": True,
    }


def _hash_user(user_id: str) -> str:
    return hashlib.sha256(f"suh:{user_id}".encode("utf-8")).hexdigest()[:16]
