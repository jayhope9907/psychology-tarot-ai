import pytest
from fastapi.testclient import TestClient

from app.assessments import ALL_INSTRUMENTS, ASSESSMENT_DOMAINS
from app.main import app
from app.services.assessment_battery import (
    boost_battery_coverage_scores,
    build_battery_status,
    next_recommended_instruments,
)
from app.services.assessment_selector import select_best_assessment
from app.services.chat_session import ChatSessionState


def test_catalog_covers_all_domains_and_instruments():
    registered = set(ALL_INSTRUMENTS.keys())
    from_registry = set()
    for meta in ASSESSMENT_DOMAINS.values():
        from_registry.update(meta["instruments"])
    assert registered == from_registry
    assert len(ASSESSMENT_DOMAINS) >= 12
    assert len(ALL_INSTRUMENTS) >= 13


def test_battery_status_empty_session():
    state = ChatSessionState(user_id="battery-empty")
    status = build_battery_status(state)

    assert status["domains_total"] == len(ASSESSMENT_DOMAINS)
    assert status["overall_completion_rate"] == 0.0
    assert status["instruments_touched"] == 0
    assert len(status["domains"]) == len(ASSESSMENT_DOMAINS)


def test_battery_status_partial_progress():
    state = ChatSessionState(user_id="battery-partial")
    state.formal_answers["phq9"] = {"phq9_q1": 2, "phq9_q2": 1}
    state.formal_answers["gad7"] = {"gad7_q1": 1}

    status = build_battery_status(state)

    assert status["instruments_touched"] == 2
    assert status["overall_completion_rate"] > 0
    mood_domain = next(d for d in status["domains"] if d["domain_id"] == "clinical_mood")
    assert mood_domain["instruments"][0]["completion_rate"] > 0


def test_boost_prefers_untouched_domains():
    state = ChatSessionState(user_id="battery-boost")
    state.turn_count = 3
    state.formal_answers["phq9"] = {
        "phq9_q1": 1,
        "phq9_q2": 1,
        "phq9_q3": 1,
        "phq9_q4": 1,
        "phq9_q5": 1,
    }
    base = {"phq9": 0.5, "isi": 0.5}
    boosted = boost_battery_coverage_scores(state, base)

    assert boosted["isi"] > boosted["phq9"]


def test_boost_prefers_in_progress_instrument():
    state = ChatSessionState(user_id="battery-continue")
    state.formal_answers["phq9"] = {"phq9_q1": 2}
    state.turn_count = 4

    selection = select_best_assessment(state, "그냥 이야기하고 싶어요.")

    assert selection is not None
    assert selection.instrument_id == "phq9"


def test_recommendations_lists_pending_items():
    state = ChatSessionState(user_id="battery-rec")
    recs = next_recommended_instruments(state, limit=3)

    assert len(recs) == 3
    assert all("instrument_id" in r for r in recs)
    assert all("domain_label" in r for r in recs)


def test_catalog_api():
    client = TestClient(app)
    response = client.get("/api/v1/assessments/catalog")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_instruments"] == len(ALL_INSTRUMENTS)
    assert payload["total_domains"] == len(ASSESSMENT_DOMAINS)


def test_battery_api_not_found():
    client = TestClient(app)
    response = client.get("/api/v1/assessments/battery/missing-session")
    assert response.status_code == 404


def test_assessment_submit_api():
    from app.services.chat_session import ChatSessionState, CHAT_SESSIONS

    state = ChatSessionState(user_id="submit-user")
    CHAT_SESSIONS[state.session_id] = state
    client = TestClient(app)

    response = client.post(
        "/api/v1/assessments/submit",
        json={
            "user_id": "submit-user",
            "session_id": state.session_id,
            "instrument": "phq9",
            "item_id": "phq9_q1",
            "value": 2,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recorded"]["recorded"] is True
    assert body["battery_coverage"]["instruments_touched"] == 1

    CHAT_SESSIONS.pop(state.session_id, None)
