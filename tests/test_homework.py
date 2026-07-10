from app.services.chat_session import ChatSessionState, clear_sessions
from app.services.counseling_phase import PHASE_INTERVENTION, PHASE_TERMINATION, sync_counseling_phase
from app.services.homework import (
    build_homework_package,
    maybe_assign_homework,
    record_homework_submission,
    select_homework_types,
    should_assign_homework,
)


def setup_function():
    clear_sessions()


def test_select_homework_types_cbt():
    state = ChatSessionState(user_id="hw-cbt")
    state.preferred_school = "BECK_CBT"
    types = select_homework_types(state)
    assert "thought_record" in types
    assert "emotion_journal" in types


def test_assign_homework_on_termination():
    state = ChatSessionState(user_id="hw-term")
    state.counseling_phase = PHASE_TERMINATION
    state.turn_count = 15
    assert should_assign_homework(state) is True
    package = maybe_assign_homework(state)
    assert package
    assert len(package["assignments"]) >= 1
    assert package["assignments"][0]["title_ko"]


def test_intervention_homework_after_elapsed_turns():
    state = ChatSessionState(user_id="hw-int")
    state.counseling_phase = PHASE_INTERVENTION
    state.phase_notes["intervention_start_turn"] = 5
    state.turn_count = 7
    assert should_assign_homework(state) is True


def test_record_homework_submission_updates_summary():
    state = ChatSessionState(user_id="hw-submit")
    package = build_homework_package(state, "test")
    assignment_id = package["assignments"][0]["id"]
    result = record_homework_submission(
        state,
        assignment_id,
        {
            "today_event": "회의가 힘들었어요",
            "current_emotion": "답답함",
        },
    )
    assert result["recorded"] is True
    assert "답답함" in result["summary"]
    assert state.phase_notes.get("last_homework_summary")


def test_tarot_adds_reflection_homework():
    state = ChatSessionState(user_id="hw-tarot")
    state.tarot_handoff = {
        "cards": [{"name_ko": "탑", "psychology_theme": "위기"}],
    }
    types = select_homework_types(state)
    assert "tarot_reflection" in types


def test_sync_phase_sets_intervention_start():
    state = ChatSessionState(user_id="hw-phase")
    state.counseling_phase = PHASE_INTERVENTION
    state.turn_count = 10
    state.phase_notes["chief_complaint"] = "직장 스트레스"
    sync_counseling_phase(state, "어떻게 하면 좋을까요")
    assert state.phase_notes.get("intervention_start_turn") == 10 or state.counseling_phase == PHASE_INTERVENTION
