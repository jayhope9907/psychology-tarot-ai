"""Product line separation — consumer vs license vs disability."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_product_surfaces_api():
    res = client.get("/api/v1/product/surfaces")
    assert res.status_code == 200
    data = res.json()
    assert data["consumer_open"] is True
    ids = [line["id"] for line in data["lines"]]
    assert ids == ["consumer", "license", "disability"]
    consumer = next(l for l in data["lines"] if l["id"] == "consumer")
    routes = {r["route"] for r in consumer["routes"]}
    assert "/home" in routes
    assert "/picto" not in routes
    assert "/stealth-props" in routes
    license = next(l for l in data["lines"] if l["id"] == "license")
    assert any(r["route"] == "/theories" for r in license["routes"])
    disability = next(l for l in data["lines"] if l["id"] == "disability")
    assert disability["preview_route"] == "/disability/picto"


def test_health_includes_product_lines():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert "product_lines" in body
    assert "학회 라이선스" in body["share_links"]
    assert "장애인용(보관)" in body["share_links"]
    assert "그림 마음" not in body["share_links"]
    assert body["urls"].get("stealth_props") == "/stealth-props"
    assert "소품 카드 놀이" in body["share_links"]


def test_app_shell_includes_props_tab():
    res = client.get("/")
    assert res.status_code == 200
    assert "소품게임" in res.text
    assert 'data-tab="props"' in res.text
    assert "/stealth-props?embed=1" in res.text
    # Lazy-load: src starts blank, data-src holds the real URL
    assert 'data-src="/stealth-props?embed=1"' in res.text
    assert "about:blank" in res.text


def test_chat_embed_keeps_composer_row():
    """Dashboard must not steal the 1fr row or the chat input is clipped on phones."""
    res = client.get("/chat")
    assert res.status_code == 200
    assert "grid-template-rows: auto auto 1fr auto" in res.text
    css = client.get("/static/css/embed.css")
    assert css.status_code == 200
    assert "grid-template-rows: auto auto 1fr auto" in css.text
    assert "html.embed-mode .sidebar" in css.text
    # Phone embed: dash hidden → messages 1fr + composer auto
    assert "grid-template-rows: 1fr auto !important" in css.text.replace("\n", " ") or (
        "grid-template-rows: 1fr auto !important" in css.text
    )


def test_stealth_props_page_served():
    res = client.get("/stealth-props")
    assert res.status_code == 200
    assert "stealth-unconscious/ingest" in res.text


def test_home_has_stealth_game_entry():
    res = client.get("/home")
    assert res.status_code == 200
    assert "/stealth-props" in res.text


def test_theories_license_gate_without_key():
    res = client.get("/theories")
    assert res.status_code == 200
    assert "licenseGate" in res.text
    assert "라이선스 전용" in res.text


def test_expressive_license_gate_without_key():
    res = client.get("/expressive")
    assert res.status_code == 200
    assert "licenseGate" in res.text
