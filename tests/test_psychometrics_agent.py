from fastapi.testclient import TestClient

from app.assessments import ALL_INSTRUMENTS
from app.assessments.mbti_preference import MBTIPreferenceInstrument
from app.main import app
from app.services.chat_session import ChatSessionState
from app.services.gentle_reflection import soft_observation_line
from app.services.user_agent_algorithm import sync_agent_after_assessment


client = TestClient(app)


def test_mbti_and_abnormal_instruments_registered():
    for iid in (
        "mbti_preference",
        "ocd_probe",
        "social_anxiety_probe",
        "panic_probe",
        "mania_probe",
        "adhd_probe",
        "alcohol_probe",
        "eating_probe",
        "dissociation_probe",
        "somatic_probe",
        "anger_probe",
    ):
        assert iid in ALL_INSTRUMENTS
        assert len(ALL_INSTRUMENTS[iid].items()) >= 2


def test_mbti_score_leanings():
    inst = MBTIPreferenceInstrument()
    answers = {
        "mbti_ei_1": 3,
        "mbti_ei_2": 3,
        "mbti_sn_1": 0,
        "mbti_sn_2": 0,
        "mbti_tf_1": 3,
        "mbti_tf_2": 2,
        "mbti_jp_1": 0,
        "mbti_jp_2": 1,
    }
    scored = inst.score_partial(answers)
    assert scored["type_code_hint"]
    assert scored["non_diagnostic"] is True
    assert "I" in scored["type_code_hint"] or "?" in scored["type_code_hint"]


def test_soft_observation_phrase():
    state = ChatSessionState(user_id="soft-u", session_id="soft-s")
    state.messages = [{"role": "user", "content": "회사에서 너무 힘들고 지쳐요"}]
    line = soft_observation_line(state, "회사에서 너무 힘들고 지쳐요")
    assert "힘들" in line or "힘드" in line


def test_assessment_syncs_to_agent():
    new = client.post("/api/v1/chat/sessions/new", params={"user_id": "psych-sync-1", "plan": "PLUS"})
    assert new.status_code == 200
    sid = new.json()["session_id"]
    for item_id, value in (("mbti_ei_1", 2), ("mbti_ei_2", 3)):
        res = client.post(
            "/api/v1/assessments/submit",
            json={
                "user_id": "psych-sync-1",
                "session_id": sid,
                "instrument": "mbti_preference",
                "item_id": item_id,
                "value": value,
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body.get("agent_sync")
        assert body["agent_sync"].get("algo_id")

    agent = client.get("/api/v1/users/psych-sync-1/agent")
    assert agent.status_code == 200
    hist = agent.json()["agent_fingerprint"].get("assessment_hist") or {}
    assert "mbti_preference" in hist


def test_psychometrics_ui():
    res = client.get("/psychometrics")
    assert res.status_code == 200
    assert "MBTI" in res.text
