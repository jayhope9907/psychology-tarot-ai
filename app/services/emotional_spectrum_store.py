"""Persist unified emotional spectrum ticks for patent / B2B audit."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

from app.db.database import get_connection, init_db
from app.services.persistence import ensure_user, get_user_settings, save_user_settings

HISTORY_RING_MAX = 40
SETTINGS_KEY = "lastEmotionalSpectrum"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_spectrum_tables() -> None:
    init_db()


def persist_spectrum_tick(
    *,
    user_id: str,
    session_id: str = "",
    turn_index: int = 0,
    source: str = "chat",
    result: Mapping[str, Any],
    license_type: str = "B2C_personal",
    organization_id: Optional[str] = None,
    state: Any = None,
    age_group: Optional[str] = None,
    age_years: Optional[int] = None,
) -> Dict[str, Any]:
    ensure_spectrum_tables()
    ensure_user(user_id)

    doc = dict(result or {})
    org = organization_id or None
    when = _utc_now()
    sid = session_id or ""
    turn = max(0, int(turn_index or 0))
    src = (source or "chat").strip()[:32] or "chat"

    from app.services.dsm5_integrator import AgeGroupDataPipeline, resolve_age_group

    cohort = resolve_age_group(age_years=age_years, age_group=age_group)
    metrics = AgeGroupDataPipeline().persist_tick_metrics(
        doc,
        session_id=sid,
        age_group=cohort,
        age_years=age_years,
    )

    record = {
        "userId": user_id,
        "sessionId": sid,
        "turnIndex": turn,
        "source": src,
        "totalInternalizingScore": doc.get("total_internalizing_score"),
        "riskLevel": doc.get("internalizing_risk_level"),
        "suggestedApproach": doc.get("suggested_approach"),
        "result": doc,
        "licenseType": license_type or "B2C_personal",
        "organizationId": org,
        "ageGroup": cohort,
        "metrics": metrics,
        "recordedAt": when,
        "non_diagnostic": True,
    }

    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO emotional_spectrum_history (
                user_id, session_id, turn_index, source,
                total_score, risk_level, suggested_approach, result_json,
                license_type, organization_id, age_group, metrics_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                sid,
                turn,
                src,
                float(doc.get("total_internalizing_score") or 0.0),
                str(doc.get("internalizing_risk_level") or "NORMAL"),
                str(doc.get("suggested_approach") or ""),
                json.dumps(doc, ensure_ascii=False),
                license_type or "B2C_personal",
                org,
                cohort,
                json.dumps(metrics, ensure_ascii=False),
                when,
            ),
        )
        record["id"] = int(cur.lastrowid or 0)

        conn.execute(
            """
            UPDATE users
            SET last_spectrum_json = ?, updated_at = ?
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
            "totalInternalizingScore": record["totalInternalizingScore"],
            "riskLevel": record["riskLevel"],
            "suggestedApproach": record["suggestedApproach"],
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
            notes["emotional_spectrum"] = doc
            ring = list(notes.get("emotional_spectrum_history") or [])
            ring.append(
                {
                    "id": record.get("id"),
                    "turnIndex": turn,
                    "totalInternalizingScore": record["totalInternalizingScore"],
                    "riskLevel": record["riskLevel"],
                    "suggestedApproach": record["suggestedApproach"],
                    "recordedAt": when,
                }
            )
            notes["emotional_spectrum_history"] = ring[-HISTORY_RING_MAX:]
        except Exception:
            pass

    try:
        from app.services.psych_timeline import record_event

        record_event(
            user_id,
            "emotional_spectrum_tick",
            {
                "session_id": sid,
                "turn_index": turn,
                "source": src,
                "totalInternalizingScore": record["totalInternalizingScore"],
                "riskLevel": record["riskLevel"],
                "suggestedApproach": record["suggestedApproach"],
                "licenseType": license_type,
                "organizationId": org,
                "non_diagnostic": True,
            },
            source_id=f"esh:{sid or 'user'}:{src}:{turn}:{record.get('id')}",
            event_at=when,
        )
    except Exception:
        pass

    return record


def list_spectrum_history(
    user_id: str,
    *,
    session_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    ensure_spectrum_tables()
    lim = max(1, min(int(limit or 50), 200))
    conn = get_connection()
    try:
        if session_id:
            rows = conn.execute(
                """
                SELECT id, user_id, session_id, turn_index, source,
                       total_score, risk_level, suggested_approach, result_json,
                       license_type, organization_id, age_group, metrics_json, created_at
                FROM emotional_spectrum_history
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
                       total_score, risk_level, suggested_approach, result_json,
                       license_type, organization_id, age_group, metrics_json, created_at
                FROM emotional_spectrum_history
                WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (user_id, lim),
            ).fetchall()
        return [_row_to_public(r) for r in rows]
    finally:
        conn.close()


def list_org_spectrum_history(organization_id: str, *, limit: int = 100) -> List[Dict[str, Any]]:
    ensure_spectrum_tables()
    lim = max(1, min(int(limit or 100), 500))
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, user_id, session_id, turn_index, source,
                   total_score, risk_level, suggested_approach, result_json,
                   license_type, organization_id, age_group, metrics_json, created_at
            FROM emotional_spectrum_history
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


def get_user_last_spectrum(user_id: str) -> Optional[Dict[str, Any]]:
    ensure_spectrum_tables()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT last_spectrum_json, updated_at FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row or not row["last_spectrum_json"]:
            return None
        doc = json.loads(row["last_spectrum_json"] or "{}")
        if not doc:
            return None
        doc["updatedAt"] = row["updated_at"]
        return doc
    finally:
        conn.close()


def _row_to_public(row: Any) -> Dict[str, Any]:
    keys = set(row.keys()) if hasattr(row, "keys") else set()
    metrics = {}
    if "metrics_json" in keys and row["metrics_json"]:
        try:
            metrics = json.loads(row["metrics_json"] or "{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            metrics = {}
    return {
        "id": row["id"],
        "userId": row["user_id"],
        "sessionId": row["session_id"],
        "turnIndex": row["turn_index"],
        "source": row["source"],
        "totalInternalizingScore": row["total_score"],
        "riskLevel": row["risk_level"],
        "suggestedApproach": row["suggested_approach"],
        "result": json.loads(row["result_json"] or "{}"),
        "licenseType": row["license_type"],
        "organizationId": row["organization_id"],
        "ageGroup": row["age_group"] if "age_group" in keys else None,
        "metrics": metrics,
        "createdAt": row["created_at"],
        "non_diagnostic": True,
    }


def _hash_user(user_id: str) -> str:
    return hashlib.sha256(f"esh:{user_id}".encode("utf-8")).hexdigest()[:16]
