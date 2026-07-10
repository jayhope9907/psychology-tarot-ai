from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_test_hub_page():
    response = client.get("/test")
    assert response.status_code == 200
    assert "테스트 허브" in response.text
    assert "API 스모크 테스트" in response.text


def test_health_includes_test_url():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["urls"]["test"] == "/test"
