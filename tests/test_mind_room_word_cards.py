"""MindRoom3D wiring — word-card props + spectrum mind_room bridge."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mind_room_js_has_mindmap_props():
    src = (ROOT / "static" / "js" / "mind-room-3d.js").read_text(encoding="utf-8")
    assert "setMindmap" in src
    assert "propsGroup" in src
    assert "makeLabelSprite" in src
    assert "BackSide" in src
    # Camera starts inside the room, not outside looking at a void
    assert "_radius = 2.6" in src or "this._radius = 2.6" in src


def test_chat_wires_word_cards_into_mind_room():
    html = (ROOT / "static" / "chat.html").read_text(encoding="utf-8")
    assert "applyLive" in html
    assert "setMindmap" in html
    assert "dashMindRoom" in html
    assert "#mind-room" in html
    assert "mind-room-3d.js?v=2" in html
    assert "낱말카드" in html


def test_home_links_to_mind_room():
    html = (ROOT / "static" / "home.html").read_text(encoding="utf-8")
    assert "/chat#mind-room" in html


def test_spectrum_passes_word_cards_into_nd_matrix(tmp_path, monkeypatch):
    db = tmp_path / "mr.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    from app.db import database as dbmod

    dbmod._initialized = False
    dbmod._db_path = str(db)
    dbmod.init_db(force=True)

    from app.services.emotional_spectrum import compute_emotional_spectrum
    from app.services.word_card_mindmap import (
        analyze_conscious_boundary,
        build_mindmap_model,
        sanitize_word_card_selection,
    )
    from app.services.word_card_store import persist_word_card_tick

    class _State:
        user_id = "mr-user"
        phase_notes = {}
        persona_routing = {}

    picked = sanitize_word_card_selection(["emptiness", "joy"])
    analysis = analyze_conscious_boundary(picked)
    mindmap = build_mindmap_model(user_id="mr-user", analysis=analysis)
    persist_word_card_tick(
        user_id="mr-user",
        session_id="mr-sess",
        selection=picked,
        analysis=analysis,
        mindmap=mindmap,
    )

    state = _State()
    result = compute_emotional_spectrum(
        state=state,
        sanitized={"initialWeights": {"mood": 40, "energy": 50, "anxiety": 40}},
    )
    assert "mind_room" in result
    assert result["mind_room"]["color_tone"]
    nd = result["neurodevelopmental_matrix"]
    assert "three_d_room_fx" in nd
    assert "mind_room" in nd
    # word-card boundary should influence ND mapping (not stuck at default-only path)
    assert "spectrum_mapping" in nd
    assert result.get("mindmap") or nd.get("mindmap")


def test_integrated_model_includes_mind_room():
    from app.services.emotional_spectrum import (
        compute_emotional_spectrum,
        to_integrated_diagnostic_model,
    )

    result = compute_emotional_spectrum(
        sanitized={"initialWeights": {"mood": 20, "energy": 30, "anxiety": 70}},
    )
    model = to_integrated_diagnostic_model(result, patient_id="p1")
    assert "mind_room" in model
    assert model["mind_room"]["color_tone"] in (
        "warm-yellow",
        "cold-white",
        "dark-gray",
        "fractured-distorted",
    )
