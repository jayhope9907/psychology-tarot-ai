from fastapi.testclient import TestClient

from app.main import app
from app.services.deploy_console import deploy_status


client = TestClient(app)


def test_deploy_console_page():
    res = client.get("/deploy")
    assert res.status_code == 200
    assert "배포 콘솔" in res.text
    assert "임시 공개" in res.text


def test_deploy_status_api():
    res = client.get("/api/v1/deploy/status")
    assert res.status_code == 200
    data = res.json()
    assert data["console_route"] == "/deploy"
    assert len(data["modes"]) >= 3
    assert any(m["id"] == "tunnel" for m in data["modes"])
    assert any(m["id"] == "render" for m in data["modes"])
    assert data["render_deploy"].startswith("https://render.com/deploy")


def test_deploy_status_service_shape():
    payload = deploy_status(request_base="http://127.0.0.1:8000")
    assert payload["local_base"] == "http://127.0.0.1:8000"
    assert any(s["path"] == "/deploy" for s in payload["share_links"])


def test_health_lists_deploy_console():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["urls"]["deploy"] == "/deploy"
    assert "배포 콘솔" in body["share_links"]
