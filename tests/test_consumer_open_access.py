from fastapi.testclient import TestClient

from app.main import app
from app.services.chat_session import get_or_create_session
from app.services.consumer_access import consumer_open
from app.services.counseling_phase import assessments_unlocked


client = TestClient(app)


def test_consumer_open_enabled():
    assert consumer_open() is True


def test_session_auto_unlocks_without_payment():
    session = get_or_create_session("open-user-1", plan="FREE")
    assert session.assessment_paid is True
    assert assessments_unlocked(session) is True
    assert session.org_entitlements is None


def test_checkout_is_free_for_consumer():
    session = get_or_create_session("open-user-2", plan="FREE")
    res = client.post(
        f"/api/v1/sessions/{session.session_id}/checkout",
        json={"user_id": "open-user-2", "session_id": session.session_id, "tier_id": "standard"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body.get("consumer_open") is True or body.get("payment_required") is False


def test_associations_is_license_hub_case_notes_coming_soon():
    assoc = client.get("/associations")
    assert assoc.status_code == 200
    assert "라이선스" in assoc.text
    assert "이론" in assoc.text
    assert "미술치료" in assoc.text or "표현" in assoc.text

    notes = client.get("/case-notes")
    assert notes.status_code == 200
    assert "별도" in notes.text or "따로" in notes.text


def test_home_hides_theories_and_expressive():
    res = client.get("/home")
    assert res.status_code == 200
    assert "/theories" not in res.text
    assert "/expressive" not in res.text


def test_user_app_hides_picto_tab():
    app_page = client.get("/")
    assert app_page.status_code == 200
    assert "tabPicto" not in app_page.text
    assert 'data-tab="picto"' not in app_page.text

    stub = client.get("/picto")
    assert stub.status_code == 200
    assert "별도" in stub.text or "따로" in stub.text

    manifest = client.get("/api/v1/disability/manifest")
    assert manifest.status_code == 200
    body = manifest.json()
    assert body["user_app_exposed"] is False
    assert body["preview_route"] == "/disability/picto"


def test_clinical_catalog_open_without_license():
    res = client.get("/api/v1/clinical/catalog")
    assert res.status_code == 200
    data = res.json()
    assert len(data.get("formal_instruments") or []) >= 10
    assert not data.get("license_invalid")
