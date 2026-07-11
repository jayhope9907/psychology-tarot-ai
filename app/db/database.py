from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional

DEFAULT_DB = str(Path(__file__).resolve().parent.parent.parent / "data" / "app.db")
_db_path = os.getenv("DATABASE_PATH", DEFAULT_DB)
_initialized = False


def get_db_path() -> str:
    return _db_path


def get_connection() -> sqlite3.Connection:
    if _db_path != ":memory:":
        Path(_db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(force: bool = False) -> None:
    global _initialized
    if _initialized and not force:
        return
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                display_name TEXT,
                settings_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS session_snapshots (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_user ON session_snapshots(user_id);

            CREATE TABLE IF NOT EXISTS mood_checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                mood_score INTEGER NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                checkin_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, checkin_date),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_checkins_user_date ON mood_checkins(user_id, checkin_date);

            CREATE TABLE IF NOT EXISTS tarot_draws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                spread TEXT NOT NULL DEFAULT 'three_card',
                draw_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_tarot_user ON tarot_draws(user_id, created_at);

            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                entry_type TEXT NOT NULL DEFAULT 'homework',
                content_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

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

            CREATE TABLE IF NOT EXISTS organizations (
                org_id TEXT PRIMARY KEY,
                org_name TEXT NOT NULL,
                discipline_id TEXT NOT NULL,
                tier_id TEXT NOT NULL,
                secondary_discipline_id TEXT,
                branding_json TEXT NOT NULL DEFAULT '{}',
                contact_email TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS organization_licenses (
                license_key TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                valid_from TEXT NOT NULL,
                valid_until TEXT NOT NULL,
                seats_total INTEGER NOT NULL DEFAULT 150,
                seats_used INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (org_id) REFERENCES organizations(org_id)
            );

            CREATE INDEX IF NOT EXISTS idx_org_licenses_org ON organization_licenses(org_id);

            CREATE TABLE IF NOT EXISTS organization_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                joined_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(org_id, user_id),
                FOREIGN KEY (org_id) REFERENCES organizations(org_id)
            );
            """
        )
        conn.commit()
        _migrate_schema(conn)
        conn.commit()
        from app.services.license_store import _seed_demo_licenses

        _seed_demo_licenses(conn)
        conn.commit()
        _initialized = True
    finally:
        conn.close()


def _migrate_schema(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(mood_checkins)")}
    if "dimensions_json" not in cols:
        conn.execute(
            "ALTER TABLE mood_checkins ADD COLUMN dimensions_json TEXT NOT NULL DEFAULT '{}'"
        )


def reset_db() -> None:
    """Test helper — wipe all rows."""
    init_db(force=True)
    conn = get_connection()
    try:
        for table in (
            "organization_members",
            "organization_licenses",
            "organizations",
            "psych_timeline_events",
            "user_psych_profiles",
            "journal_entries",
            "tarot_draws",
            "mood_checkins",
            "session_snapshots",
            "users",
        ):
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
        from app.services.license_store import _seed_demo_licenses

        _seed_demo_licenses(conn)
        conn.commit()
    finally:
        conn.close()
