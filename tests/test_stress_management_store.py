import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    db = tmp_path / "stress_store.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    from app.db import database as dbmod

    dbmod._initialized = False
    dbmod._db_path = str(db)
    dbmod.init_db(force=True)
    yield str(db)
    dbmod._initialized = False


def test_persist_stress_management_tick(isolated_db):
    from app.services.stress_management_store import (
        get_user_last_stress,
        list_stress_history,
        persist_stress_management_tick,
        session_stress_summary,
    )

    record = persist_stress_management_tick(
        user_id="stress-user",
        session_id="stress-sess",
        user_message="스트레스 받아요",
        turn_index=1,
        pre_sud=6.0,
        clinical_setup={"resistance_level": "MEDIUM"},
    )
    assert record["id"] > 0
    assert record["protocolId"] == "stress_3min_reset"

    history = list_stress_history("stress-user", session_id="stress-sess")
    assert len(history) == 1
    assert history[0]["userMessageCue"].startswith("스트레스")

    summary = session_stress_summary("stress-sess")
    assert summary["tickCount"] == 1
    assert summary["precise"] is True

    latest = get_user_last_stress("stress-user")
    assert latest is not None
    assert latest.get("protocolId") == "stress_3min_reset"
