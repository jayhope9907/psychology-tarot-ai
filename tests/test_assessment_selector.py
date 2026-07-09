import pytest

from app.services.assessment_selector import select_best_assessment
from app.services.chat_session import ChatSessionState
from app.services.orchestrator import decide_turn


def test_selector_picks_gad7_for_anxiety_message():
    state = ChatSessionState(user_id="user-anxiety")
    state.turn_count = 3

    selection = select_best_assessment(state, "요즘 너무 불안하고 걱정이 멈추지 않아요. 가슴도 두근거려요.")

    assert selection is not None
    assert selection.instrument_id == "gad7"
    assert selection.item.item_id == "gad7_q1"


def test_selector_picks_phq9_for_depression_message():
    state = ChatSessionState(user_id="user-depression")
    state.turn_count = 3

    selection = select_best_assessment(state, "요즘 우울하고 무기력해서 아무것도 하기 싫어요. 흥미도 없고요.")

    assert selection is not None
    assert selection.instrument_id == "phq9"
    assert selection.item.item_id == "phq9_q1"


def test_selector_continues_in_progress_instrument():
    state = ChatSessionState(user_id="user-continue")
    state.turn_count = 5
    state.formal_answers["phq9"] = {"phq9_q1": 2}

    selection = select_best_assessment(state, "요즘 불안하기도 해요.")

    assert selection is not None
    assert selection.instrument_id == "phq9"
    assert selection.item.item_id == "phq9_q2"


def test_orchestrator_offers_assessment_on_counseling_request():
    state = ChatSessionState(user_id="user-counseling")
    state.turn_count = 3

    decision = decide_turn(state, "요즘 너무 힘들어서 상담 받고 싶어요.")

    assert decision.action == "inject_assessment"
    assert decision.selection is not None
    assert "counseling_request" in decision.reason


def test_orchestrator_skips_assessment_during_warmup_even_with_counseling_request():
    state = ChatSessionState(user_id="user-warmup")
    state.turn_count = 1

    decision = decide_turn(state, "상담이 필요해요. 너무 힘들어요.")

    assert decision.action == "chat_only"
    assert decision.reason == "warmup"
