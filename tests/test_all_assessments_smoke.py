"""Every registered instrument: items load, score runs, submit API accepts first item."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.assessments import ALL_INSTRUMENTS, ASSESSMENT_DOMAINS
from app.main import app
from app.services.chat_session import CHAT_SESSIONS, ChatSessionState


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_registry_matches_all_instruments():
    registered = set(ALL_INSTRUMENTS.keys())
    from_registry: set[str] = set()
    for meta in ASSESSMENT_DOMAINS.values():
        from_registry.update(meta["instruments"])
    assert registered == from_registry
    assert len(ALL_INSTRUMENTS) >= 60


def test_all_instruments_items_and_score():
    for instrument_id, instrument in ALL_INSTRUMENTS.items():
        items = instrument.items()
        assert items, f"{instrument_id} has no items"
        first = items[0]
        score = instrument.score_partial({first.item_id: 1})
        assert score["instrument"] == instrument_id
        assert score["completed_items"] >= 1


def test_submit_first_item_each_instrument(client: TestClient):
    state = ChatSessionState(user_id="smoke-all-instruments")
    CHAT_SESSIONS[state.session_id] = state
    try:
        for instrument_id, instrument in ALL_INSTRUMENTS.items():
            first = instrument.items()[0]
            response = client.post(
                "/api/v1/assessments/submit",
                json={
                    "user_id": state.user_id,
                    "session_id": state.session_id,
                    "instrument": instrument_id,
                    "item_id": first.item_id,
                    "value": 1,
                },
            )
            assert response.status_code == 200, f"{instrument_id}: {response.text}"
            assert response.json()["recorded"]["recorded"] is True
    finally:
        CHAT_SESSIONS.pop(state.session_id, None)
