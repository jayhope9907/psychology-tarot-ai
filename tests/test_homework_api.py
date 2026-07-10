from fastapi.testclient import TestClient

from app.main import app
from app.services.chat_session import ChatSessionState, clear_sessions
from app.services.counseling_phase import PHASE_TERMINATION
from app.services.homework import build_homework_package


client = TestClient(app)


def setup_function():
    clear_sessions()


def test_homework_submit_endpoint():
    state = ChatSessionState(user_id="api-hw")
    from app.services.chat_session import CHAT_SESSIONS

    CHAT_SESSIONS[state.session_id] = state
    state.counseling_phase = PHASE_TERMINATION
    package = build_homework_package(state)
    assignment_id = package["assignments"][0]["id"]

    response = client.post(
        f"/api/v1/sessions/{state.session_id}/homework/submit",
        json={
            "user_id": "api-hw",
            "session_id": state.session_id,
            "assignment_id": assignment_id,
            "responses": {
                "today_event": "오늘 회의가 힘들었어요",
                "current_emotion": "불안",
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["recorded"] is True


def test_homework_list_endpoint():
    state = ChatSessionState(user_id="api-hw-list")
    from app.services.chat_session import CHAT_SESSIONS

    CHAT_SESSIONS[state.session_id] = state
    build_homework_package(state)

    response = client.get(f"/api/v1/sessions/{state.session_id}/homework")
    assert response.status_code == 200
    assert response.json()["completed_count"] == 0
