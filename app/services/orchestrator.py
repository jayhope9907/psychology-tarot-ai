from __future__ import annotations



from dataclasses import dataclass

from typing import Any, Dict, List, Optional



from app.assessments import ALL_INSTRUMENTS

from app.assessments.base import AssessmentItem
from app.assessments.user_voice import enrich_assessment_payload

from app.services.assessment_battery import next_recommended_instruments, sync_session_battery

from app.services.assessment_directing import build_efficacy_card
from app.services.clinical_insight import sync_session_insight

from app.services.counseling_phase import (
    PHASE_ASSESSMENT_BRIEFING,
    assessments_unlocked,
    phase_allows_assessment,
    phase_snapshot,
    sync_counseling_phase,
)

from app.services.assessment_selector import select_best_assessment

from app.services.chat_session import ChatSessionState

from app.services.fatigue_manager import (

    detect_assessment_request,

    detect_counseling_request,

    detect_distress,

    fatigue_snapshot,

    session_has_assessment_intent,

    session_has_distress,

    should_block_new_assessment,

)





@dataclass

class OrchestratorDecision:

    action: str

    assessment: Optional[Dict[str, Any]] = None

    fatigue: Optional[Dict[str, Any]] = None

    reason: str = ""

    selection: Optional[Dict[str, Any]] = None





def _serialize_assessment(item: AssessmentItem, optional: bool = True, selection: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:

    payload = {

        "instrument": item.instrument,

        "item_id": item.item_id,

        "prompt": item.prompt,

        "response_type": item.response_type.value,

        "options": item.options,

        "optional": optional,

        "framing": item.conversational_framing or "잠깐만요, 마음을 더 잘 이해하려고 가볍게 여쭤볼게요.",

        "counselor_note": "답하지 않으셔도 괜찮아요. 편하신 만큼만 나눠 주세요.",

    }

    if selection:

        payload["selection"] = selection

    enriched = enrich_assessment_payload(payload)
    instrument_id = str(enriched.get("instrument") or item.instrument or "")
    if instrument_id:
        card = build_efficacy_card(instrument_id)
        enriched["efficacy"] = {
            "headline": card.get("headline"),
            "affirmation": card.get("affirmation"),
            "strength_prompt": card.get("strength_prompt"),
            "seeds": card.get("seeds") or [],
            "how_to": card.get("how_to"),
            "disclaimer": card.get("disclaimer"),
        }
        enriched["coach_line"] = card.get("affirmation") or enriched.get("counselor_note")
    return enriched





def _should_offer_assessment(state: ChatSessionState, user_message: str) -> bool:

    if not phase_allows_assessment(state, user_message):

        return False

    if detect_assessment_request(user_message) or session_has_assessment_intent(state, user_message):

        return state.turn_count >= 2

    if state.counseling_phase == "assessment":

        return state.turn_count >= 3

    if state.turn_count < 4:

        return False

    if detect_distress(user_message) or session_has_distress(state, user_message):

        return True

    if detect_counseling_request(user_message):

        return True

    return state.turn_count >= 5





def _is_battery_gap_fill(state: ChatSessionState, instrument_id: str, scores: Dict[str, float]) -> bool:

    recommendations = next_recommended_instruments(state, limit=1)

    if not recommendations or recommendations[0]["instrument_id"] != instrument_id:

        return False

    if recommendations[0]["completion_rate"] > 0:

        return False

    return scores.get(instrument_id, 0.0) < 2.0





def decide_turn(

    state: ChatSessionState,

    user_message: str,

    assessment_response: Optional[Dict[str, Any]] = None,

    client: Any = None,

) -> OrchestratorDecision:

    sync_counseling_phase(state, user_message)
    fatigue = fatigue_snapshot(state, user_message)



    if assessment_response:

        sync_session_battery(state)

        return OrchestratorDecision(action="chat_only", fatigue=fatigue, reason="assessment_answer_recorded")



    if state.counseling_phase == PHASE_ASSESSMENT_BRIEFING and not assessments_unlocked(state):

        return OrchestratorDecision(action="chat_only", fatigue=fatigue, reason="awaiting_payment")



    if should_block_new_assessment(state, user_message):

        reason = "warmup" if state.turn_count <= 1 and not session_has_distress(state, user_message) else "fatigue_or_spacing"

        if fatigue["blocked"]:

            reason = "fatigue_limit"

        elif state.pending_assessment:

            reason = "pending_assessment"

        elif detect_assessment_request(user_message) and state.assessments_offered >= 3:

            reason = "assessment_limit"

        return OrchestratorDecision(action="chat_only", fatigue=fatigue, reason=reason)



    if not _should_offer_assessment(state, user_message):

        return OrchestratorDecision(action="chat_only", fatigue=fatigue, reason="conversation_first")



    selection = select_best_assessment(state, user_message, client)

    if not selection:

        return OrchestratorDecision(action="chat_only", fatigue=fatigue, reason="no_available_assessment")



    selection_meta = {

        "instrument_id": selection.instrument_id,

        "confidence": selection.confidence,

        "method": selection.method,

        "rationale": selection.rationale,

        "scores": selection.scores,

    }

    assessment = _serialize_assessment(selection.item, optional=True, selection=selection_meta)



    if detect_assessment_request(user_message) or session_has_assessment_intent(state, user_message):

        reason = "user_requested_assessment"

    elif detect_distress(user_message) or session_has_distress(state, user_message):

        reason = "distress_matched_assessment"

    elif selection.method == "ai":

        reason = "ai_matched_assessment"

    else:

        reason = "rule_matched_assessment"



    if _is_battery_gap_fill(state, selection.instrument_id, selection.scores):

        reason = "battery_gap_fill"

    elif detect_counseling_request(user_message):

        reason = f"counseling_request_{reason}"



    return OrchestratorDecision(

        action="inject_assessment",

        assessment=assessment,

        fatigue=fatigue,

        reason=reason,

        selection=selection_meta,

    )





def record_assessment_offer(state: ChatSessionState, assessment: Dict[str, Any]) -> None:

    state.assessments_offered += 1

    state.last_assessment_turn = state.turn_count

    state.pending_assessment = assessment





def record_assessment_answer(state: ChatSessionState, assessment_response: Dict[str, Any]) -> Dict[str, Any]:

    instrument = str(assessment_response.get("instrument") or "")

    item_id = str(assessment_response.get("item_id") or "")

    value = assessment_response.get("value")

    text_value = assessment_response.get("text")

    skipped = bool(assessment_response.get("skipped"))

    if not skipped and instrument and state.org_entitlements:
        from app.services.association_licensing import instrument_allowed

        if not instrument_allowed(instrument, state.org_entitlements):
            return {"recorded": False, "error": "not_licensed"}

    if skipped:

        state.assessments_skipped += 1

        state.pending_assessment = None

        state.fatigue_score = min(1.0, state.fatigue_score + 0.05)

        sync_session_battery(state)

        sync_session_insight(state)

        return {"recorded": False, "skipped": True}



    if value is None and text_value is not None:

        value = str(text_value).strip()

    if value is None or (isinstance(value, str) and not value):

        return {"recorded": False, "skipped": False}



    if isinstance(value, str):

        result = {

            "recorded": True,

            "instrument": instrument,

            "item_id": item_id,

            "value": value,

            "text": value,

        }

        instrument_impl = ALL_INSTRUMENTS.get(instrument)

        if instrument_impl:

            answers = state.formal_answers.setdefault(instrument, {})

            answers[item_id] = value

            result["formal_score"] = instrument_impl.score_partial(answers)

        else:

            state.micro_answers.append(

                {"instrument": instrument, "item_id": item_id, "value": value, "text": value}

            )

        state.assessments_completed += 1

        state.pending_assessment = None

        state.fatigue_score = max(0.0, state.fatigue_score - 0.04)

        sync_session_battery(state)

        sync_session_insight(state)

        return result



    numeric_value = int(value)

    result: Dict[str, Any] = {

        "recorded": True,

        "instrument": instrument,

        "item_id": item_id,

        "value": numeric_value,

    }



    instrument_impl = ALL_INSTRUMENTS.get(instrument)

    if instrument_impl:

        answers = state.formal_answers.setdefault(instrument, {})

        answers[item_id] = numeric_value

        result["formal_score"] = instrument_impl.score_partial(answers)

    else:

        state.micro_answers.append(

            {

                "instrument": instrument,

                "item_id": item_id,

                "value": numeric_value,

            }

        )



    state.assessments_completed += 1

    state.pending_assessment = None

    state.fatigue_score = max(0.0, state.fatigue_score - 0.04)

    sync_session_battery(state)

    sync_session_insight(state)

    return result





def build_profile_delta(state: ChatSessionState) -> Dict[str, Any]:

    formal_scores: Dict[str, Any] = {}

    for instrument_id, answers in state.formal_answers.items():

        instrument = ALL_INSTRUMENTS.get(instrument_id)

        if instrument and answers:

            formal_scores[instrument_id] = instrument.score_partial(answers)



    battery = sync_session_battery(state)

    insight = sync_session_insight(state)



    return {

        "session_id": state.session_id,

        "turn_count": state.turn_count,

        "formal_scores": formal_scores,

        "micro_answers": list(state.micro_answers),

        "fatigue": fatigue_snapshot(state),

        "battery_coverage": battery,

        "battery_recommendations": next_recommended_instruments(state, limit=5),

        "clinical_insight": insight,

        "counseling_phase": phase_snapshot(state),

    }


