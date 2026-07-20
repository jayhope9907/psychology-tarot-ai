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
            "stress_management_history",
            "clinical_adaptive_history",
            "word_card_mindmap_history",
            "emotional_spectrum_history",
            "user_emotional_patterns",
            "psych_timeline_events",
        }
        missing = required - tables
        if missing:
            print("FAIL missing tables:", missing)
            return 1
        user_cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
        for col in ("last_sanitized_json", "consultation_mode", "last_stress_json", "last_clinical_adaptive_json", "last_mindmap_json", "last_spectrum_json"):
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
    importlib.import_module("app.services.stress_management")
    importlib.import_module("app.services.stress_management_store")
    importlib.import_module("app.services.clinical_adaptive_store")
    importlib.import_module("app.services.word_card_mindmap")
    importlib.import_module("app.services.word_card_store")
    importlib.import_module("app.services.emotional_spectrum")
    importlib.import_module("app.services.emotional_spectrum_store")
    main_mod = importlib.import_module("app.main")
    assert getattr(main_mod, "app", None) is not None
    routes = {getattr(r, "path", None) for r in main_mod.app.routes}
    for path in (
        "/api/v1/users/{user_id}/sanitized-input",
        "/api/v1/users/{user_id}/sanitized-input/history",
        "/api/v1/orgs/{org_id}/sanitized-input/history",
        "/api/v1/users/{user_id}/stress-management",
        "/api/v1/users/{user_id}/stress-management/history",
        "/api/v1/orgs/{org_id}/stress-management/history",
        "/api/v1/users/{user_id}/clinical-adaptive",
        "/api/v1/users/{user_id}/clinical-adaptive/history",
        "/api/v1/orgs/{org_id}/clinical-adaptive/history",
        "/api/v1/word-cards/deck",
        "/api/v1/users/{user_id}/word-cards",
        "/api/v1/users/{user_id}/word-cards/history",
        "/api/v1/users/{user_id}/mindmap",
        "/api/v1/users/{user_id}/emotional-spectrum",
        "/api/v1/users/{user_id}/emotional-spectrum/history",
        "/api/v1/users/{user_id}/integrated-diagnostic",
        "/api/v1/orgs/{org_id}/emotional-spectrum/history",
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

    from app.services.stress_management_store import persist_stress_management_tick, session_stress_summary
    from app.services.clinical_adaptive_store import persist_clinical_adaptive_tick

    persist_stress_management_tick(
        user_id="build-check-user",
        session_id="build-check-sess",
        user_message="스트레스 받아요",
        turn_index=2,
    )
    sm_summary = session_stress_summary("build-check-sess")
    if sm_summary.get("tickCount") != 1:
        print("FAIL stress tracking", sm_summary)
        return 1

    persist_clinical_adaptive_tick(
        user_id="build-check-user",
        session_id="build-check-sess",
        turn_index=2,
        resistance_level="HIGH",
        cognitive_level="SIMPLE_EASY",
    )
    print("OK stress + clinical adaptive persist")

    from app.services.word_card_mindmap import (
        analyze_conscious_boundary,
        build_mindmap_model,
        sanitize_word_card_selection,
    )
    from app.services.word_card_store import persist_word_card_tick, list_word_card_history

    picked = sanitize_word_card_selection(["emptiness", "joy", "free text is dropped"])
    wc_analysis = analyze_conscious_boundary(picked)
    mindmap = build_mindmap_model(user_id="build-check-user", analysis=wc_analysis)
    persist_word_card_tick(
        user_id="build-check-user",
        session_id="build-check-sess",
        turn_index=3,
        selection=picked,
        analysis=wc_analysis,
        mindmap=mindmap,
    )
    wc_history = list_word_card_history("build-check-user", session_id="build-check-sess")
    if len(wc_history) != 1 or wc_history[0]["selectedCards"] != ["emptiness", "joy"]:
        print("FAIL word card tracking", wc_history)
        return 1
    print("OK word card + mindmap persist")

    from app.services.emotional_spectrum import compute_emotional_spectrum
    from app.services.emotional_spectrum_store import persist_spectrum_tick, list_spectrum_history

    spectrum = compute_emotional_spectrum(
        sanitized={"initialWeights": {"mood": 20, "energy": 30, "anxiety": 80}},
        behavioral_metrics={"hesitation_index": 0.6, "backspace_count": 10, "word_delay_ms": 3000},
    )
    if "mind_room" not in spectrum or spectrum["internalizing_risk_level"] not in ("NORMAL", "MONITOR", "HIGH_ALERT"):
        print("FAIL spectrum compute", spectrum)
        return 1
    persist_spectrum_tick(
        user_id="build-check-user",
        session_id="build-check-sess",
        turn_index=4,
        result=spectrum,
    )
    es_history = list_spectrum_history("build-check-user", session_id="build-check-sess")
    if len(es_history) != 1:
        print("FAIL spectrum tracking", es_history)
        return 1
    print("OK emotional spectrum persist")
    print("BUILD CHECK PASSED")
    try:
        db_path.unlink(missing_ok=True)
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
