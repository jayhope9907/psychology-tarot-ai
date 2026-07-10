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
            """
        )
        conn.commit()
        _initialized = True
    finally:
        conn.close()


def reset_db() -> None:
    """Test helper — wipe all rows."""
    init_db(force=True)
    conn = get_connection()
    try:
        for table in ("journal_entries", "tarot_draws", "mood_checkins", "session_snapshots", "users"):
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
    finally:
        conn.close()
