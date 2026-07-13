"""Layered assessment directing + self-efficacy seed persistence."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.assessments import ALL_INSTRUMENTS, ASSESSMENT_DOMAINS
from app.main import app
from app.services.assessment_directing import build_assessment_directing, build_efficacy_card
from app.services.chat_session import CHAT_SESSIONS, ChatSessionState


client = TestClient(app)


def test_directing_layers_for_every_instrument():
    for iid in ALL_INSTRUMENTS:
        d = build_assessment_directing(iid, item_index=0, completed=False)
        assert d["active_layer"] in {"orient", "progress", "efficacy"}
        assert set(d["layers"].keys()) == {"arrival", "orient", "progress", "complete", "efficacy"}
        assert d["coach_line"]
        done = build_assessment_directing(iid, item_index=0, completed=True)
        assert done["active_layer"] == "efficacy"
        assert done["layers"]["efficacy"]["seeds"]


def test_self_efficacy_instrument_registered():
    assert "self_efficacy_gse" in ALL_INSTRUMENTS
    assert "self_efficacy_gse" in ASSESSMENT_DOMAINS["wellbeing_self"]["instruments"]


def test_catalog_includes_directing():
    res = client.get("/api/v1/clinical/catalog")
    assert res.status_code == 200
    data = res.json()
    sample = next(i for i in data["formal_instruments"] if i["instrument_id"] == "rses")
    assert sample.get("directing")
    assert sample["directing"]["layers"]["arrival"]
    assert sample.get("efficacy_preview", {}).get("seeds")


def test_submit_returns_directing_and_efficacy_seed_saves():
    state = ChatSessionState(user_id="dir-eff-user")
    CHAT_SESSIONS[state.session_id] = state
    try:
        instrument = ALL_INSTRUMENTS["rses"]
        items = instrument.items()
        for idx, item in enumerate(items):
            res = client.post(
                "/api/v1/assessments/submit",
                json={
                    "user_id": state.user_id,
                    "session_id": state.session_id,
                    "instrument": "rses",
                    "item_id": item.item_id,
                    "value": 2,
                    "item_index": idx,
                    "finished": idx == len(items) - 1,
                },
            )
            assert res.status_code == 200
            body = res.json()
            assert "directing" in body
            if idx == len(items) - 1:
                assert body.get("efficacy")
                assert body["efficacy"]["seeds"]
        card = build_efficacy_card("rses")
        seed = card["seeds"][0]
        res2 = client.post(
            "/api/v1/assessments/efficacy-seed",
            json={
                "user_id": state.user_id,
                "session_id": state.session_id,
                "instrument": "rses",
                "seed": seed,
                "strength_note": "오늘 버텼어요",
            },
        )
        assert res2.status_code == 200
        assert res2.json()["saved"] is True
        assert state.phase_notes.get("last_efficacy", {}).get("seed") == seed
    finally:
        CHAT_SESSIONS.pop(state.session_id, None)
