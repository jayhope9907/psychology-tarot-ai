from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_new_session_and_transcript():
    user = "session-api-user"
    create = client.post(f"/api/v1/chat/sessions/new?user_id={user}")
    assert create.status_code == 200
    session_id = create.json()["session_id"]

    stream = client.post(
        "/api/v1/chat/stream",
        json={
            "user_id": user,
            "session_id": session_id,
            "message": "안녕하세요, 요즘 마음이 무거워요.",
            "plan": "BASIC",
        },
        headers={"Accept": "text/event-stream"},
    )
    assert stream.status_code == 200

    transcript = client.get(f"/api/v1/chat/sessions/{session_id}/transcript")
    assert transcript.status_code == 200
    payload = transcript.json()
    assert payload["session_id"] == session_id
    assert len(payload["messages"]) >= 2
    assert payload["messages"][0]["role"] == "user"

    listed = client.get(f"/api/v1/chat/sessions/user/{user}")
    assert listed.status_code == 200
    sessions = listed.json()["sessions"]
    assert any(s["session_id"] == session_id for s in sessions)
