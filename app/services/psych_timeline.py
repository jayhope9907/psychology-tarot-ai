"""Longitudinal psych events and user profile storage."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.db.database import get_connection, init_db
from app.services.persistence import ensure_user


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_tables() -> None:
    init_db()
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS psych_timeline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                source_id TEXT NOT NULL DEFAULT '',
                event_at TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, event_type, source_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_psych_timeline_user
                ON psych_timeline_events(user_id, event_at DESC);

            CREATE TABLE IF NOT EXISTS user_psych_profiles (
                user_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def record_event(
    user_id: str,
    event_type: str,
    payload: Dict[str, Any],
    *,
    event_at: Optional[str] = None,
    source_id: str = "",
) -> int:
    _ensure_tables()
    ensure_user(user_id)
    when = event_at or _utc_now()
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO psych_timeline_events
                (user_id, event_type, source_id, event_at, payload_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, event_type, source_id) DO UPDATE SET
                event_at = excluded.event_at,
                payload_json = excluded.payload_json
            """,
            (user_id, event_type, source_id or "", when, json.dumps(payload, ensure_ascii=False)),
        )
        conn.commit()
        return int(cur.lastrowid or 0)
    finally:
        conn.close()


def list_events(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    _ensure_tables()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, event_type, source_id, event_at, payload_json, created_at
            FROM psych_timeline_events
            WHERE user_id = ?
            ORDER BY event_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        out: List[Dict[str, Any]] = []
        for row in rows:
            out.append(
                {
                    "id": row["id"],
                    "event_type": row["event_type"],
                    "source_id": row["source_id"],
                    "event_at": row["event_at"],
                    "payload": json.loads(row["payload_json"] or "{}"),
                    "created_at": row["created_at"],
                }
            )
        return out
    finally:
        conn.close()


def save_profile(user_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_tables()
    ensure_user(user_id)
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO user_psych_profiles (user_id, profile_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                profile_json = excluded.profile_json,
                updated_at = excluded.updated_at
            """,
            (user_id, json.dumps(profile, ensure_ascii=False), _utc_now()),
        )
        conn.commit()
        return profile
    finally:
        conn.close()


def load_profile(user_id: str) -> Optional[Dict[str, Any]]:
    _ensure_tables()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT profile_json, updated_at FROM user_psych_profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        profile = json.loads(row["profile_json"] or "{}")
        profile["updated_at"] = row["updated_at"]
        return profile
    finally:
        conn.close()


def clear_user_psych_data(user_id: str) -> None:
    _ensure_tables()
    conn = get_connection()
    try:
        conn.execute("DELETE FROM psych_timeline_events WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM user_psych_profiles WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()
