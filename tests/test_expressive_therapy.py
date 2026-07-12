from fastapi.testclient import TestClient

from app.main import app
from app.services.expressive_therapy import MODES, expressive_catalog
from app.services.persona_router import route_clinical_persona


client = TestClient(app)


def test_expressive_catalog_has_modes_and_scholars():
    catalog = expressive_catalog()
    assert len(catalog["modes"]) >= 6
    assert {m["mode_id"] for m in catalog["modes"]} == set(MODES.keys())
    assert len(catalog["scholars"]) >= 4
    names = {s["id"] for s in catalog["scholars"]}
    assert {"moreno", "perls", "naumburg", "kramer"} <= names
    assert len(catalog.get("art_techniques") or []) >= 8


def test_expressive_catalog_api():
    res = client.get("/api/v1/expressive/catalog")
    assert res.status_code == 200
    data = res.json()
    assert "disclaimer" in data
    assert data["safety"]["stop_anytime"] is True


def test_empty_chair_flow_and_stop():
    start = client.post(
        "/api/v1/expressive/start",
        json={"user_id": "ex-user-1", "mode_id": "empty_chair"},
    )
    assert start.status_code == 200
    body = start.json()
    assert body["ok"] is True
    assert body["session"]["school"] == "GESTALT"
    sid = body["session_id"]
    ex_id = body["session"]["session_id"]

    step1 = client.post(
        "/api/v1/expressive/step",
        json={
            "user_id": "ex-user-1",
            "session_id": sid,
            "expressive_session_id": ex_id,
            "response": {"choice": "시작할래요"},
        },
    )
    assert step1.status_code == 200
    assert step1.json()["step"]["step_id"] == "place"

    stop = client.post(
        "/api/v1/expressive/step",
        json={
            "user_id": "ex-user-1",
            "session_id": sid,
            "expressive_session_id": ex_id,
            "stop": True,
        },
    )
    assert stop.status_code == 200
    assert stop.json()["stopped"] is True


def test_role_play_picto_stop():
    start = client.post(
        "/api/v1/expressive/start",
        json={"user_id": "ex-user-2", "mode_id": "role_play"},
    )
    assert start.status_code == 200
    body = start.json()
    assert body["session"]["school"] == "PSYCHODRAMA"
    stop = client.post(
        "/api/v1/expressive/step",
        json={
            "user_id": "ex-user-2",
            "session_id": body["session_id"],
            "expressive_session_id": body["session"]["session_id"],
            "response": {"picto_id": "stop"},
        },
    )
    assert stop.status_code == 200
    assert stop.json()["stopped"] is True


def test_route_psychodrama_keywords():
    routing = route_clinical_persona("역할극으로 해보고 싶어요. 빈 의자 기법도요.")
    assert routing["school"].value in ("PSYCHODRAMA", "GESTALT", "DRAMA_THERAPY")


def test_expressive_ui_route():
    res = client.get("/expressive")
    assert res.status_code == 200
    assert "표현" in res.text or "역할" in res.text
