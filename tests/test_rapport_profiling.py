import pytest

from app.services.chat_session import ChatSessionState, clear_sessions
from app.services.counseling_phase import PHASE_ASSESSMENT_BRIEFING, PHASE_RAPPORT, sync_counseling_phase
from app.services.rapport_profiling import is_rapport_complete, rapport_readiness, update_client_profile


@pytest.fixture(autouse=True)
def reset():
    clear_sessions()
    yield
    clear_sessions()


def _rich_messages_state(state: ChatSessionState, turn_count: int = 3) -> ChatSessionState:
    state.turn_count = turn_count
    state.messages = [
        {"role": "user", "content": "최근 회사 일이 너무 버거워요"},
        {"role": "assistant", "content": "많이 힘드시겠어요"},
        {"role": "user", "content": "우울하고 밤에 잠도 못 자서 일상이 많이 힘들어요"},
    ]
    update_client_profile(state, "우울하고 밤에 잠도 못 자서 일상이 많이 힘들어요")
    return state


def test_single_greeting_not_rapport_ready():
    state = ChatSessionState(user_id="rapport-1")
    state.turn_count = 1

    readiness = rapport_readiness(state, "안녕하세요")

    assert not readiness["ready"]
    assert readiness["score"] < 0.72


def test_insufficient_profile_stays_in_rapport():
    state = ChatSessionState(user_id="rapport-2")
    state.turn_count = 2
    state.messages = [{"role": "user", "content": "우울해요"}]

    sync_counseling_phase(state, "마음이 답답해요")

    assert state.counseling_phase == PHASE_RAPPORT


def test_full_profile_completes_rapport():
    state = ChatSessionState(user_id="rapport-3")
    _rich_messages_state(state, turn_count=3)

    assert is_rapport_complete(state, "며칠째 회사에서 불안하고 지장이 커요")

    sync_counseling_phase(state, "며칠째 회사에서 불안하고 지장이 커요")

    assert state.counseling_phase == PHASE_ASSESSMENT_BRIEFING


def test_rapport_tracks_missing_items():
    state = ChatSessionState(user_id="rapport-4")
    state.turn_count = 2
    state.messages = [{"role": "user", "content": "요즘 우울해요"}]

    readiness = rapport_readiness(state, "그냥 힘들어요")

    assert not readiness["ready"]
    assert readiness["missing"]
