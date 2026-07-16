"""B2B high-risk (SOS) alerts for society master dashboards.

Uses an durable SQLite inbox (pollable). Designed so a future WebSocket
fan-out can subscribe to the same `org_sos_alerts` rows.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.db.database import get_connection, init_db
from app.models.commercial_license import is_b2b_license, normalize_license_type
from app.services.b2b_privacy import anonymize_messages, anonymize_pii
from app.services.persistence import ensure_user

# Thresholds (non-diagnostic wellness / educational escalation)
SUD_CRISIS_THRESHOLD = 7.5
DRYNESS_SCORE_THRESHOLD = 0.45
DISTORTION_BURST_THRESHOLD = 4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_sos_tables() -> None:
    init_db()
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS org_sos_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id TEXT NOT NULL,
                user_id_hash TEXT NOT NULL,
                session_id TEXT NOT NULL DEFAULT '',
                license_type TEXT NOT NULL,
                consultation_mode TEXT NOT NULL DEFAULT 'psychology',
                alert_level TEXT NOT NULL DEFAULT 'elevated',
                reason_codes_json TEXT NOT NULL DEFAULT '[]',
                payload_json TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                acked_at TEXT,
                acked_by TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_sos_org_status
                ON org_sos_alerts(org_id, status, created_at DESC);
            """
        )
        conn.commit()
    finally:
        conn.close()


def _user_hash(user_id: str) -> str:
    import hashlib

    return "u_" + hashlib.sha256((user_id or "anon").encode("utf-8")).hexdigest()[:16]


def evaluate_sos_triggers(
    *,
    pattern_analysis: Optional[Dict[str, Any]] = None,
    mode_analyzer: Optional[Dict[str, Any]] = None,
    latest_sud: Optional[float] = None,
) -> Dict[str, Any]:
    reasons: List[str] = []
    analysis = pattern_analysis or {}
    analyzer = mode_analyzer or {}

    if analysis.get("inEmotionalCrisisVsBaseline"):
        reasons.append("baseline_emotional_crisis")
    latest = latest_sud
    if latest is None:
        latest = analysis.get("latestDistress")
    if isinstance(latest, (int, float)) and float(latest) >= SUD_CRISIS_THRESHOLD:
        reasons.append("sud_above_threshold")

    dryness = (analyzer.get("spiritualDryness") or {}) if analyzer else {}
    if dryness.get("detected") and float(dryness.get("score") or 0) >= DRYNESS_SCORE_THRESHOLD:
        reasons.append("spiritual_dryness")

    flags = analyzer.get("cognitiveDistortionFlags") or analysis.get("topDistortions") or []
    if isinstance(flags, list) and len(flags) >= DISTORTION_BURST_THRESHOLD:
        reasons.append("distortion_burst")

    level = "critical" if "sud_above_threshold" in reasons or "spiritual_dryness" in reasons else "elevated"
    return {
        "should_alert": bool(reasons),
        "alert_level": level if reasons else "none",
        "reason_codes": reasons,
        "thresholds": {
            "sud": SUD_CRISIS_THRESHOLD,
            "spiritual_dryness": DRYNESS_SCORE_THRESHOLD,
            "distortion_burst": DISTORTION_BURST_THRESHOLD,
        },
        "non_diagnostic": True,
    }


def enqueue_org_sos_alert(
    *,
    org_id: str,
    user_id: str,
    license_type: str,
    consultation_mode: str = "psychology",
    session_id: str = "",
    evaluation: Dict[str, Any],
    messages: Optional[List[Dict[str, Any]]] = None,
    pattern_summary_ko: str = "",
) -> Optional[Dict[str, Any]]:
    if not org_id or not evaluation.get("should_alert"):
        return None
    if not is_b2b_license(license_type):
        return None

    ensure_sos_tables()
    ensure_user(user_id)

    masked_bundle = anonymize_messages(messages or [])
    summary_masked, _ = anonymize_pii(pattern_summary_ko or "")

    payload = {
        "patternSummaryKo": summary_masked,
        "reason_codes": evaluation.get("reason_codes") or [],
        "alert_level": evaluation.get("alert_level"),
        "masked_transcript_tail": (masked_bundle.get("messages") or [])[-6:],
        "pii_hit_counts": masked_bundle.get("pii_hit_counts") or {},
        "event": "org_sos_alert",
        "channel_hint": "poll_or_websocket",
        "non_diagnostic": True,
    }

    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO org_sos_alerts (
                org_id, user_id_hash, session_id, license_type, consultation_mode,
                alert_level, reason_codes_json, payload_json, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                org_id,
                _user_hash(user_id),
                session_id or "",
                normalize_license_type(license_type),
                consultation_mode or "psychology",
                evaluation.get("alert_level") or "elevated",
                json.dumps(evaluation.get("reason_codes") or [], ensure_ascii=False),
                json.dumps(payload, ensure_ascii=False),
                _utc_now(),
            ),
        )
        conn.commit()
        alert_id = cur.lastrowid
    finally:
        conn.close()

    return {
        "id": alert_id,
        "org_id": org_id,
        "user_id_hash": _user_hash(user_id),
        "status": "pending",
        "alert_level": evaluation.get("alert_level"),
        "reason_codes": evaluation.get("reason_codes"),
        "payload": payload,
        "created_at": _utc_now(),
        "delivery": {
            "websocket_event": "org_sos_alert",
            "poll_url": f"/api/v1/orgs/{org_id}/sos-alerts?status=pending",
        },
    }


def list_org_sos_alerts(
    org_id: str,
    *,
    status: str = "pending",
    limit: int = 50,
) -> List[Dict[str, Any]]:
    ensure_sos_tables()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, org_id, user_id_hash, session_id, license_type, consultation_mode,
                   alert_level, reason_codes_json, payload_json, status, created_at, acked_at, acked_by
            FROM org_sos_alerts
            WHERE org_id = ? AND (? = 'all' OR status = ?)
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (org_id, status, status, max(1, min(200, int(limit)))),
        ).fetchall()
    finally:
        conn.close()

    out: List[Dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "id": row["id"],
                "org_id": row["org_id"],
                "user_id_hash": row["user_id_hash"],
                "session_id": row["session_id"],
                "licenseType": row["license_type"],
                "consultationMode": row["consultation_mode"],
                "alert_level": row["alert_level"],
                "reason_codes": json.loads(row["reason_codes_json"] or "[]"),
                "payload": json.loads(row["payload_json"] or "{}"),
                "status": row["status"],
                "created_at": row["created_at"],
                "acked_at": row["acked_at"],
                "acked_by": row["acked_by"],
            }
        )
    return out


def ack_org_sos_alert(org_id: str, alert_id: int, *, acked_by: str = "dashboard") -> Dict[str, Any]:
    ensure_sos_tables()
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE org_sos_alerts
            SET status = 'acked', acked_at = ?, acked_by = ?
            WHERE id = ? AND org_id = ?
            """,
            (_utc_now(), acked_by, alert_id, org_id),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "id": alert_id, "org_id": org_id, "status": "acked"}


def maybe_trigger_b2b_sos(
    *,
    license_type: str,
    org_id: Optional[str],
    user_id: str,
    consultation_mode: str,
    session_id: str = "",
    pattern_analysis: Optional[Dict[str, Any]] = None,
    mode_analyzer: Optional[Dict[str, Any]] = None,
    latest_sud: Optional[float] = None,
    messages: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """Middleware-style entry: only fires for non-B2C licenses with org_id."""
    if not is_b2b_license(license_type) or not org_id:
        return None
    evaluation = evaluate_sos_triggers(
        pattern_analysis=pattern_analysis,
        mode_analyzer=mode_analyzer,
        latest_sud=latest_sud,
    )
    if not evaluation.get("should_alert"):
        return None
    return enqueue_org_sos_alert(
        org_id=org_id,
        user_id=user_id,
        license_type=license_type,
        consultation_mode=consultation_mode,
        session_id=session_id,
        evaluation=evaluation,
        messages=messages,
        pattern_summary_ko=(pattern_analysis or {}).get("patternReportKo") or "",
    )
