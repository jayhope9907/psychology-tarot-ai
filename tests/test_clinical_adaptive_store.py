import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    db = tmp_path / "clinical_adaptive.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    from app.db import database as dbmod

    dbmod._initialized = False
    dbmod._db_path = str(db)
    dbmod.init_db(force=True)
    yield str(db)
    dbmod._initialized = False


def test_persist_clinical_adaptive_tick(isolated_db):
    from app.services.clinical_adaptive_store import (
        get_user_last_clinical_adaptive,
        list_clinical_adaptive_history,
        persist_clinical_adaptive_tick,
        session_clinical_adaptive_summary,
    )

    record = persist_clinical_adaptive_tick(
        user_id="ca-user",
        session_id="ca-sess",
        turn_index=2,
        resistance_level="HIGH",
        sensory_impairment_deaf=True,
        cognitive_level="SIMPLE_EASY",
    )
    assert record["id"] > 0
    setup = record["clinicalAdaptiveSetup"]
    assert setup["adaptive_enabled"] is True
    assert setup["resistance_level"] == "HIGH"

    history = list_clinical_adaptive_history("ca-user", session_id="ca-sess")
    assert len(history) == 1
    assert history[0]["adaptiveEnabled"] is True

    summary = session_clinical_adaptive_summary("ca-sess")
    assert summary["tickCount"] == 1
    assert summary["adaptiveEnabledCount"] == 1

    latest = get_user_last_clinical_adaptive("ca-user")
    assert latest["clinicalAdaptiveSetup"]["cognitive_level"] == "SIMPLE_EASY"
