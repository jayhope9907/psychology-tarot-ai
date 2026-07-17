import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    db = tmp_path / "spectrum.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    from app.db import database as dbmod

    dbmod._initialized = False
    dbmod._db_path = str(db)
    dbmod.init_db(force=True)
    yield str(db)
    dbmod._initialized = False


def test_persist_spectrum_tick(isolated_db):
    from app.services.emotional_spectrum import compute_emotional_spectrum
    from app.services.emotional_spectrum_store import (
        get_user_last_spectrum,
        list_spectrum_history,
        persist_spectrum_tick,
    )

    result = compute_emotional_spectrum(
        sanitized={"initialWeights": {"mood": 15, "energy": 25, "anxiety": 85}},
        behavioral_metrics={"hesitation_index": 0.7, "backspace_count": 12},
    )
    record = persist_spectrum_tick(
        user_id="es-user",
        session_id="es-sess",
        turn_index=1,
        result=result,
    )
    assert record["id"] > 0
    assert record["riskLevel"] in ("NORMAL", "MONITOR", "HIGH_ALERT")

    history = list_spectrum_history("es-user", session_id="es-sess")
    assert len(history) == 1
    assert history[0]["result"]["mind_room"]["color_tone"] in (
        "warm-yellow",
        "dark-gray",
        "fractured-distorted",
    )

    latest = get_user_last_spectrum("es-user")
    assert latest is not None
    assert latest["total_internalizing_score"] == result["total_internalizing_score"]
