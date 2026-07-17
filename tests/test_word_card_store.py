import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    db = tmp_path / "word_card.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    from app.db import database as dbmod

    dbmod._initialized = False
    dbmod._db_path = str(db)
    dbmod.init_db(force=True)
    yield str(db)
    dbmod._initialized = False


def test_persist_word_card_tick(isolated_db):
    from app.services.word_card_mindmap import (
        analyze_conscious_boundary,
        build_mindmap_model,
        sanitize_word_card_selection,
    )
    from app.services.word_card_store import (
        get_user_last_mindmap,
        list_word_card_history,
        persist_word_card_tick,
    )

    picked = sanitize_word_card_selection(["emptiness", "joy"])
    analysis = analyze_conscious_boundary(picked)
    mindmap = build_mindmap_model(user_id="wc-user", analysis=analysis)

    record = persist_word_card_tick(
        user_id="wc-user",
        session_id="wc-sess",
        turn_index=1,
        selection=picked,
        analysis=analysis,
        mindmap=mindmap,
    )
    assert record["id"] > 0
    assert record["selectedCards"] == ["emptiness", "joy"]

    history = list_word_card_history("wc-user", session_id="wc-sess")
    assert len(history) == 1
    assert history[0]["mindmap"]["centerNodeId"] == "me_now"
    assert history[0]["boundaryScore"] == analysis["boundaryScore"]

    latest = get_user_last_mindmap("wc-user")
    assert latest is not None
    assert latest["centerNodeId"] == "me_now"
