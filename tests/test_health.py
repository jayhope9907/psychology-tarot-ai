from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["urls"]["home"] == "/"
    assert payload["urls"]["chat"] == "/chat"
    assert payload["urls"]["tarot"] == "/tarot"
    assert payload["urls"]["test"] == "/test"
    assert payload["share_links"]["3D 타로"] == "/tarot"
    assert "render.com/deploy" in payload["deploy_hint"]
