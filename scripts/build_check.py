"""Local build / migration verification (no network)."""
from __future__ import annotations

import compileall
import importlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    db_path = ROOT / "data" / f"build_check_{stamp}.db"
    os.environ["DATABASE_PATH"] = str(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print("== compileall app ==")
    ok = compileall.compile_dir(str(ROOT / "app"), quiet=1, force=True)
    if not ok:
        print("FAIL: compileall")
        return 1
    print("OK compileall")

    sys.path.insert(0, str(ROOT))
    print("== import app.main ==")
    # Reset init flag if re-imported
    from app.db import database as dbmod

    dbmod._initialized = False
    dbmod._db_path = str(db_path)
    init_db = dbmod.init_db
    init_db(force=True)

    conn = dbmod.get_connection()
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {
            "users",
            "session_snapshots",
            "sanitized_input_history",
            "user_emotional_patterns",
            "psych_timeline_events",
        }
        missing = required - tables
        if missing:
            print("FAIL missing tables:", missing)
            return 1
        user_cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
        for col in ("last_sanitized_json", "consultation_mode"):
            if col not in user_cols:
                print("FAIL users missing", col)
                return 1
        sess_cols = {r[1] for r in conn.execute("PRAGMA table_info(session_snapshots)")}
        for col in (
            "last_sanitized_json",
            "consultation_mode",
            "current_step",
            "resistance_level",
            "sensory_impairment_deaf",
            "cognitive_level",
        ):
            if col not in sess_cols:
                print("FAIL session_snapshots missing", col)
                return 1
    finally:
        conn.close()
    print("OK schema migration")

    print("== import FastAPI app ==")
    # Avoid binding side effects; just import module
    importlib.import_module("app.services.sanitized_input_store")
    importlib.import_module("app.services.input_sanitizer")
    importlib.import_module("app.services.clinical_adaptor")
    main_mod = importlib.import_module("app.main")
    assert getattr(main_mod, "app", None) is not None
    routes = {getattr(r, "path", None) for r in main_mod.app.routes}
    for path in (
        "/api/v1/users/{user_id}/sanitized-input",
        "/api/v1/users/{user_id}/sanitized-input/history",
        "/api/v1/orgs/{org_id}/sanitized-input/history",
    ):
        if path not in routes:
            print("FAIL missing route", path)
            return 1
    print("OK routes")

    from app.services.input_sanitizer import sanitize_and_compensate
    from app.services.sanitized_input_store import persist_sanitized_input, session_tracking_summary

    snap = sanitize_and_compensate(
        {"consultationMode": "psychology", "step": 2, "selectedCard": "Strength", "checkInMetrics": None}
    )
    persist_sanitized_input(
        user_id="build-check-user",
        session_id="build-check-sess",
        sanitized=snap,
        turn_index=1,
        source="chat",
    )
    summary = session_tracking_summary("build-check-sess")
    if summary.get("tickCount") != 1 or not summary.get("precise"):
        print("FAIL tracking", summary)
        return 1
    print("OK sanitized persist + tracking")
    print("BUILD CHECK PASSED")
    try:
        db_path.unlink(missing_ok=True)
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
