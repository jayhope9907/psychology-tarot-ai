import pytest

from app.services.case_preview import build_case_preview
from app.services.chat_session import ChatSessionState, clear_sessions


@pytest.fixture(autouse=True)
def reset():
    clear_sessions()
    yield
    clear_sessions()


def test_depression_case_classification():
    state = ChatSessionState(user_id="case-depression")
    state.turn_count = 2
    state.phase_notes = {"chief_complaint": "지금 제가 우울증이 있고 무기력해요"}

    preview = build_case_preview(
        state,
        "마음이 답답하고 아무것도 하기 싫어요",
        ranked_instruments=[
            {"instrument_id": "phq9", "score": 3.2},
            {"instrument_id": "gad7", "score": 0.5},
        ],
    )

    assert preview["hypotheses"]
    assert preview["hypotheses"][0]["case_id"] == "depressive"
    assert preview["future_vision"]
    assert preview["defense_points"]
    assert "스크리닝" in preview["disclaimer"]


def test_relationship_case_in_hypotheses():
    state = ChatSessionState(user_id="case-relation")
    state.turn_count = 2
    state.phase_notes = {"chief_complaint": "대인관계가 너무 힘들어요"}

    preview = build_case_preview(
        state,
        "사람들과 거리를 두고 싶어요",
        ranked_instruments=[
            {"instrument_id": "attachment_ecr", "score": 2.8},
            {"instrument_id": "phq9", "score": 0.4},
        ],
    )

    case_ids = [row["case_id"] for row in preview["hypotheses"]]
    assert "relational" in case_ids
