from fastapi.testclient import TestClient

from app.main import app
from app.services.daily_routine import compute_streak, record_checkin, today_checkin
from app.services.insights import build_weekly_report, suggest_homework_intensity
from app.services.persistence import load_latest_session_for_user, save_session
from app.services.chat_session import ChatSessionState, get_or_create_session

client = TestClient(app)


def test_home_route():
    res = client.get("/home")
    assert res.status_code == 200
    assert "마음 체크인" in res.text or "마음쉼터" in res.text


def test_app_route():
    res = client.get("/")
    assert res.status_code == 200
    assert "app-shell" in res.text


def test_chat_route():
    response = client.get("/chat")
    assert response.status_code == 200
    assert "마음쉼터" in response.text


def test_checkin_and_streak():
    user = "daily-user-1"
    first = record_checkin(user, 4, "괜찮아요")
    assert first["streak_days"] >= 1
    assert today_checkin(user)["mood_score"] == 4
    second = record_checkin(user, 3, "수정")
    assert second["mood_score"] == 3
    streak = compute_streak(user)
    assert streak["current_streak"] >= 1


def test_dashboard_api():
    user = "daily-user-2"
    record_checkin(user, 5, "좋아요")
    response = client.get(f"/api/v1/dashboard/{user}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["today_checkin"]["mood_score"] == 5
    assert "greeting" in payload
    assert "weekly_report" in payload


def test_session_persistence():
    user = "persist-user"
    state = ChatSessionState(user_id=user, session_id="sess-persist-1")
    state.messages.append({"role": "user", "content": "안녕"})
    state.turn_count = 1
    save_session(state)

    loaded = get_or_create_session(user, "sess-persist-1")
    assert loaded.turn_count == 1
    assert loaded.messages[0]["content"] == "안녕"


def test_history_api():
    user = "history-user"
    record_checkin(user, 2, "힘듦")
    response = client.get(f"/api/v1/history/{user}")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["checkins"]) >= 1


def test_weekly_report_empty():
    report = build_weekly_report("brand-new-user")
    assert "summary" in report


def test_homework_intensity_suggestion():
    user = "hw-intensity"
    record_checkin(user, 1)
    record_checkin(user, 2)
    assert suggest_homework_intensity(user) == "light"
