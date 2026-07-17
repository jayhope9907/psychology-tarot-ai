"""Persist word-card picks + mindmap snapshots for patent / B2B audit."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

from app.db.database import get_connection, init_db
from app.services.persistence import ensure_user, get_user_settings, save_user_settings

HISTORY_RING_MAX = 40
SETTINGS_KEY = "lastWordCardMindmap"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_word_card_tables() -> None:
    init_db()


def persist_word_card_tick(
    *,
    user_id: str,
    session_id: str = "",
    turn_index: int = 0,
    source: str = "chat",
    selection: Optional[List[Mapping[str, Any]]] = None,
    analysis: Optional[Mapping[str, Any]] = None,
    mindmap: Optional[Mapping[str, Any]] = None,
    license_type: str = "B2C_personal",
    organization_id: Optional[str] = None,
    state: Any = None,
) -> Dict[str, Any]:
    ensure_word_card_tables()
    ensure_user(user_id)

    sel = [dict(c) for c in (selection or [])]
    ana = dict(analysis or {})
    mm = dict(mindmap or {})
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
        "selectedCards": [c.get("id") for c in sel],
        "boundaryScore": ana.get("boundaryScore"),
        "analysis": ana,
        "mindmap": mm,
        "licenseType": license_type or "B2C_personal",
        "organizationId": org,
        "recordedAt": when,
        "non_diagnostic": True,
    }

    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO word_card_mindmap_history (
                user_id, session_id, turn_index, source,
                selected_cards_json, boundary_score, analysis_json, mindmap_json,
                license_type, organization_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                sid,
                turn,
                src,
                json.dumps([c.get("id") for c in sel], ensure_ascii=False),
                float(ana.get("boundaryScore") or 0.5),
                json.dumps(ana, ensure_ascii=False),
                json.dumps(mm, ensure_ascii=False),
                license_type or "B2C_personal",
                org,
                when,
            ),
        )
        record["id"] = int(cur.lastrowid or 0)

        conn.execute(
            """
            UPDATE users
            SET last_mindmap_json = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (json.dumps(mm, ensure_ascii=False), when, user_id),
        )
        conn.commit()
    finally:
        conn.close()

    try:
        settings = get_user_settings(user_id)
        settings[SETTINGS_KEY] = {
            "selectedCards": record["selectedCards"],
            "boundaryScore": record["boundaryScore"],
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
            notes["word_card_analysis"] = ana
            notes["mindmap"] = mm
            ring = list(notes.get("word_card_history") or [])
            ring.append(
                {
                    "id": record.get("id"),
                    "turnIndex": turn,
                    "selectedCards": record["selectedCards"],
                    "boundaryScore": record["boundaryScore"],
                    "recordedAt": when,
                }
            )
            notes["word_card_history"] = ring[-HISTORY_RING_MAX:]
        except Exception:
            pass

    try:
        from app.services.psych_timeline import record_event

        record_event(
            user_id,
            "word_card_tick",
            {
                "session_id": sid,
                "turn_index": turn,
                "source": src,
                "selectedCards": record["selectedCards"],
                "boundaryScore": record["boundaryScore"],
                "licenseType": license_type,
                "organizationId": org,
                "non_diagnostic": True,
            },
            source_id=f"wch:{sid or 'user'}:{src}:{turn}:{record.get('id')}",
            event_at=when,
        )
    except Exception:
        pass

    return record


def list_word_card_history(
    user_id: str,
    *,
    session_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    ensure_word_card_tables()
    lim = max(1, min(int(limit or 50), 200))
    conn = get_connection()
    try:
        if session_id:
            rows = conn.execute(
                """
                SELECT id, user_id, session_id, turn_index, source,
                       selected_cards_json, boundary_score, analysis_json, mindmap_json,
                       license_type, organization_id, created_at
                FROM word_card_mindmap_history
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
                       selected_cards_json, boundary_score, analysis_json, mindmap_json,
                       license_type, organization_id, created_at
                FROM word_card_mindmap_history
                WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (user_id, lim),
            ).fetchall()
        return [_row_to_public(r) for r in rows]
    finally:
        conn.close()


def get_user_last_mindmap(user_id: str) -> Optional[Dict[str, Any]]:
    ensure_word_card_tables()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT last_mindmap_json, updated_at FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row or not row["last_mindmap_json"]:
            return None
        mm = json.loads(row["last_mindmap_json"] or "{}")
        if not mm:
            return None
        mm["updatedAt"] = row["updated_at"]
        return mm
    finally:
        conn.close()


def _row_to_public(row: Any) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "userId": row["user_id"],
        "sessionId": row["session_id"],
        "turnIndex": row["turn_index"],
        "source": row["source"],
        "selectedCards": json.loads(row["selected_cards_json"] or "[]"),
        "boundaryScore": row["boundary_score"],
        "analysis": json.loads(row["analysis_json"] or "{}"),
        "mindmap": json.loads(row["mindmap_json"] or "{}"),
        "licenseType": row["license_type"],
        "organizationId": row["organization_id"],
        "createdAt": row["created_at"],
        "non_diagnostic": True,
    }


def _hash_user(user_id: str) -> str:
    return hashlib.sha256(f"wch:{user_id}".encode("utf-8")).hexdigest()[:16]
