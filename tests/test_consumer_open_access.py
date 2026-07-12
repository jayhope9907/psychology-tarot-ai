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


def test_associations_and_case_notes_show_coming_soon():
    for path in ("/associations", "/case-notes"):
        res = client.get(path)
        assert res.status_code == 200
        assert "별도" in res.text or "따로" in res.text


def test_clinical_catalog_open_without_license():
    res = client.get("/api/v1/clinical/catalog")
    assert res.status_code == 200
    data = res.json()
    assert len(data.get("formal_instruments") or []) >= 10
    assert not data.get("license_invalid")
