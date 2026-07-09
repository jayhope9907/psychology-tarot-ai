import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.chat_session import ChatSessionState, CHAT_SESSIONS
from app.services.clinical_insight import build_clinical_insight


def test_insight_insufficient_without_data():
    state = ChatSessionState(user_id="insight-empty")
    insight = build_clinical_insight(state)

    assert insight["overall_zone"] == "insufficient_data"
    assert insight["professional_care_probability"] == 0.0
    assert insight["ready_for_interpretation"] is False


def test_insight_normal_for_low_phq9_scores():
    state = ChatSessionState(user_id="insight-normal")
    state.turn_count = 5
    state.formal_answers["phq9"] = {"phq9_q1": 0, "phq9_q2": 1, "phq9_q3": 0}

    insight = build_clinical_insight(state)

    assert insight["overall_zone"] in {"normal", "mild_elevation", "insufficient_data"}
    assert insight["normal_range_probability"] >= 0.0


def test_insight_elevated_for_depression_and_anxiety():
    state = ChatSessionState(user_id="insight-elevated")
    state.turn_count = 8
    state.formal_answers["phq9"] = {"phq9_q1": 3, "phq9_q2": 3, "phq9_q3": 2, "phq9_q4": 2, "phq9_q5": 2}
    state.formal_answers["gad7"] = {"gad7_q1": 3, "gad7_q2": 2, "gad7_q3": 3, "gad7_q4": 2}

    insight = build_clinical_insight(state)

    assert insight["professional_care_probability"] >= 0.35
    assert insight["overall_zone"] in {"mild_elevation", "clinical_concern"}
    assert insight["recommendation_tier"] in {
        "counseling_suggested",
        "clinical_evaluation_recommended",
        "urgent_care_suggested",
    }
    assert "스크리닝" in insight["disclaimer"] or "진단" in insight["disclaimer"]


def test_insights_api():
    state = ChatSessionState(user_id="insight-api")
    state.formal_answers["phq9"] = {"phq9_q1": 2, "phq9_q2": 2}
    CHAT_SESSIONS[state.session_id] = state

    client = TestClient(app)
    response = client.get(f"/api/v1/insights/{state.session_id}")

    assert response.status_code == 200
    body = response.json()
    assert "summary_ko" in body
    assert "professional_care_probability" in body

    CHAT_SESSIONS.pop(state.session_id, None)
