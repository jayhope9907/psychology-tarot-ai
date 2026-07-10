from __future__ import annotations

import asyncio
import json
import re
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from app.models.clinical import ClinicalSchool
from app.prompt_config import COUNSELOR_NAME, build_chat_system_prompt
from app.services.chat_session import ChatSessionState
from app.services.assessment_package import build_assessment_package, mark_package_presented
from app.services.counseling_phase import (
    PHASE_ASSESSMENT_BRIEFING,
    build_phase_prompt,
    is_rapport_complete,
    phase_snapshot,
    rapport_readiness,
    sync_counseling_phase,
)
from app.services.fatigue_manager import (
    detect_assessment_request,
    detect_distress,
    session_has_assessment_intent,
    session_has_distress,
)
from app.services.orchestrator import (
    OrchestratorDecision,
    build_profile_delta,
    decide_turn,
    record_assessment_answer,
    record_assessment_offer,
)
from app.services.homework import build_homework_chat_context, maybe_assign_homework, record_homework_submission
from app.services.tarot_bridge import build_tarot_system_block, should_suggest_tarot
from app.services.persona_router import build_persona_directive, route_clinical_persona
from app.services.prompt_binding import PromptContextWeightBindingFactory, extract_chat_quant_features

INSTRUMENT_LABELS = {
    "phq9": "우울 척도(PHQ-9)",
    "gad7": "불안 척도(GAD-7)",
    "attachment_ecr": "관계·애착",
    "isi": "수면",
    "pss": "스트레스",
    "micro_emotion": "감정 온도",
}


def _instrument_label(instrument_id: str) -> str:
    return INSTRUMENT_LABELS.get(instrument_id, "마음 상태")


def _last_assistant_message(state: ChatSessionState) -> str:
    for entry in reversed(state.messages):
        if entry.get("role") == "assistant":
            return (entry.get("content") or "").strip()
    return ""


def _is_near_duplicate(candidate: str, previous: str) -> bool:
    if not candidate or not previous:
        return False
    if candidate == previous:
        return True
    shorter, longer = (candidate, previous) if len(candidate) <= len(previous) else (previous, candidate)
    if len(shorter) >= 24 and shorter in longer:
        return True
    return False


def _is_short_follow_up(user_message: str) -> bool:
    text = (user_message or "").strip()
    if len(text) > 28:
        return False
    markers = ("네", "맞", "응", "그래", "맞아", "맞아요", "네요", "그렇", "맞습니다")
    return len(text) <= 14 or any(marker in text for marker in markers)


def _workplace_context(state: ChatSessionState, user_message: str) -> bool:
    blob = f"{user_message} {state.phase_notes.get('chief_complaint', '')}".lower()
    return any(keyword in blob for keyword in ("직장", "회사", "상사", "동료", "업무", "일"))


def _conceptualization_reply(state: ChatSessionState, user_message: str) -> str:
    chief = (state.phase_notes.get("chief_complaint") or "지금 이야기").strip()
    notes = state.phase_notes

    if _is_short_follow_up(user_message):
        if _workplace_context(state, user_message):
            return (
                "직장에서 힘드셨군요. 그때 구체적으로 어떤 일이 있었는지, "
                "가장 마음에 남는 순간 하나만 들려주실 수 있을까요?"
            )
        return (
            "네, 말씀해 주신 마음 이어서 들어볼게요. "
            "그 상황에서 몸이나 마음에 가장 먼저 올라온 느낌은 어땠나요?"
        )

    if notes.get("conceptualization_intro_done"):
        return (
            "조금 더 구체적으로 함께 짚어볼게요. "
            "그때 특히 힘들었던 장면이나, "
            "마음속에 떠오르는 생각이 있다면 편하게 말씀해 주세요."
        )

    notes["conceptualization_intro_done"] = True
    return (
        f"'{chief[:36]}' 이야기를 들으니, "
        "비슷한 마음이 반복될 수 있겠다는 생각이 들어요. "
        "그때 가장 크게 느껴지는 감정은 무엇에 가깝나요?"
    )


def _anti_repeat_reply(
    user_message: str,
    state: ChatSessionState,
    decision: Optional[OrchestratorDecision] = None,
    assessment_response: Optional[Dict[str, Any]] = None,
    blocked: str = "",
) -> str:
    """Generate a fresh reply when the candidate duplicates the previous turn."""
    if state.counseling_phase == "conceptualization":
        state.phase_notes["conceptualization_intro_done"] = True
        return _conceptualization_reply(state, user_message)

    if _workplace_context(state, user_message) or "직장" in user_message:
        return (
            "직장에서의 그 마음, 충분히 무겁게 느껴져요. "
            "오늘 있었던 일 중에서 특히 마음이 무거웠던 순간이 있다면 들려주실 수 있을까요?"
        )

    if detect_distress(user_message) or session_has_distress(state, user_message):
        return (
            "힘드시다는 말씀, 잘 전해졌어요. "
            "그 마음이 올라올 때 몸에서는 어떻게 느껴지나요? "
            "편한 만큼만 더 들려주셔도 괜찮아요."
        )

    if _is_short_follow_up(user_message):
        return (
            "네, 이어서 들어볼게요. "
            "방금 말씀하신 상황에서 가장 먼저 떠오르는 감정이나 생각이 있다면 무엇인가요?"
        )

    return (
        "말씀해 주셔서 고마워요. "
        "방금 이야기를 조금만 더 구체적으로 들려주시면, "
        "지금 마음을 더 잘 이해하는 데 큰 도움이 될 것 같아요."
    )


def fallback_reply(
    user_message: str,
    state: ChatSessionState,
    decision: Optional[OrchestratorDecision] = None,
    assessment_response: Optional[Dict[str, Any]] = None,
) -> str:
    from app.services.mood_assistant import (
        build_assessment_briefing_reply,
        mood_priority_reply,
        resolve_mood_context,
    )

    ctx = resolve_mood_context(state.user_id)
    mood_reply = mood_priority_reply(ctx, state, user_message, decision, assessment_response)
    if mood_reply:
        return mood_reply

    if state.counseling_phase == "rapport" and not detect_distress(user_message) and not detect_assessment_request(user_message):
        return (
            "안녕하세요, 편하게 오신 것만으로도 큰 용기예요. "
            "이곳은 비밀이 보장되고, 편한 속도로 이야기할 수 있는 공간이에요. "
            "지금 가장 먼저 나누고 싶은 마음이 있다면 들려주세요."
        )

    if state.counseling_phase == "termination":
        return (
            "그동안 나눠 주신 이야기와 마음, 정말 소중했어요. "
            "오늘 함께 살펴본 변화를 마음에 간직하시고, "
            "힘들 때는 1393·전문 상담기관에도 언제든 연락하셔도 괜찮아요. "
            "스스로를 돌보는 작은 한 걸음, 오늘도 응원해요."
        )

    if state.counseling_phase == "conceptualization" and state.phase_notes.get("chief_complaint"):
        return _conceptualization_reply(state, user_message)

    if state.counseling_phase == "intervention" and state.phase_notes.get("goals"):
        goal = state.phase_notes["goals"][0]
        return (
            f"함께 정한 방향인 '{goal}'을 위해, "
            "오늘 당장 시도해 볼 수 있는 아주 작은 한 걸음을 생각해 볼까요? "
            "예를 들어 5분 산책, 감정을 한 줄 적기처럼 부담 없는 것도 좋아요."
        )

    if state.counseling_phase == "rapport" and not is_rapport_complete(state, user_message):
        readiness = rapport_readiness(state, user_message)
        missing = readiness["missing"][0] if readiness["missing"] else "지금 마음"
        return (
            "천천히 들려주셔서 고마워요. 아직은 검사보다, "
            f"{missing.replace('고객의 구체적 이야기를 2회 이상 더 들어주세요', '이야기')}에 "
            "조금 더 귀 기울이고 싶어요. 편한 만큼만 더 들려주실 수 있을까요?"
        )

    if state.counseling_phase == PHASE_ASSESSMENT_BRIEFING:
        package = state.assessment_package or {}
        if package:
            return build_assessment_briefing_reply(ctx, package)
        return (
            "지금까지 이야기를 바탕으로 맞춤 검사 패키지를 준비했어요. "
            "아래 카드에서 구성을 확인하시고, 준비되시면 이어서 진행하실 수 있어요."
        )

    if assessment_response and assessment_response.get("skipped"):
        return (
            "네, 지금은 넘어가도 괜찮아요. "
            "말씀해 주신 마음은 충분히 중요해요. "
            "우울한 기분이 가장 크게 느껴지는 순간이 언제인지, 편하실 때 조금만 더 들려주실 수 있을까요?"
        )

    if assessment_response and assessment_response.get("value") is not None:
        return (
            "답해 주셔서 고마워요. 방금 답변을 바탕으로 지금 상태를 조금씩 그려가고 있어요. "
            "검사가 쌓일수록 정상 범주인지, 전문 상담이 도움이 될지 더 정확히 안내해 드릴 수 있어요. "
            "그때 가장 먼저 떠오르는 생각이나 감정이 있다면 함께 나눠 주세요."
        )

    if decision and decision.action == "inject_assessment" and decision.selection:
        instrument_id = decision.selection.get("instrument_id", "")
        label = _instrument_label(instrument_id)
        if detect_assessment_request(user_message) or session_has_assessment_intent(state, user_message):
            return (
                f"네, 검사 가능해요. 지금 말씀해 주신 마음을 더 잘 이해하려고 "
                f"{label}에서 가볍게 한 가지만 여쭤볼게요. "
                "아래에서 편한 만큼만 골라 주시면, 대화가 이어지는 동안 결과도 차곡차곡 쌓여요. "
                "진단이 아니라 참고용 스크리닝이에요."
            )
        if session_has_distress(state, user_message) or detect_distress(user_message):
            return (
                f"말씀해 주신 우울한 마음, 충분히 느껴졌어요. "
                f"감정만으로 단정하기 어려워서, {label}으로 지금 상태를 가볍게 확인해 보려고 해요. "
                "아래 질문 하나만 편하게 답해 주셔도 돼요."
            )
        return (
            f"대화를 이어가면서 {label} 질문 하나 드릴게요. "
            "편한 만큼만 선택해 주시면, 정상 범주인지 전문 상담이 필요한지도 함께 살펴볼 수 있어요."
        )

    if detect_assessment_request(user_message):
        return (
            "네, 검사·상태 확인은 가능해요. "
            "대화 속에서 PHQ·GAD 같은 표준 도구를 짧게 진행하고, "
            "정상 범주인지 전문 상담·병원 평가가 필요한지 확률로 안내해 드릴게요. "
            "지금 가장 불편한 마음부터 조금만 더 들려주실 수 있을까요?"
        )

    if detect_distress(user_message):
        if "우울" in user_message:
            return (
                "우울하다고 말씀해 주신 것만으로도 큰 용기예요. "
                "그 마음이 언제부터, 어떤 상황에서 특히 크게 느껴지는지 들려주실 수 있을까요? "
                "원하시면 대화 중에 우울 척도도 가볍게 함께 확인해 드릴 수 있어요."
            )
        if "답답" in user_message:
            return (
                "답답한 마음이 느껴져요. 가슴이 조이거나 숨이 얕아지는 느낌처럼, "
                "몸에서는 어떻게 느껴지는지도 궁금해요. "
                "그 답답함이 가장 크게 올라올 때가 있다면 언제인가요?"
            )
        return (
            "지금 많이 힘드신 것 같아요. 그 감정을 느끼게 된 계기나 "
            "하루 중 가장 버거운 순간이 있다면 편하게 말씀해 주세요."
        )

    if "관계" in user_message or "대인" in user_message:
        return (
            "관계 이야기군요. 사람과의 연결에서 오는 기분은 마음 전체에 큰 영향을 주죠. "
            "요즘 관계에서 가장 마음에 걸리는 부분이 무엇인지 들려주실 수 있을까요?"
        )

    return (
        "천천히 들려주셔서 고마워요. "
        "지금 이 순간, 가장 먼저 풀고 싶은 마음이나 궁금한 점이 있다면 무엇인가요?"
    )


def enrich_assistant_reply(
    text: str,
    user_message: str,
    state: ChatSessionState,
    decision: Optional[OrchestratorDecision] = None,
    assessment_response: Optional[Dict[str, Any]] = None,
) -> str:
    """Replace thin or off-topic model output with contextual fallback."""
    cleaned = (text or "").strip()
    fallback = fallback_reply(user_message, state, decision, assessment_response)

    if not cleaned:
        return fallback

    if detect_assessment_request(user_message):
        if "가능" not in cleaned and "검사" not in cleaned:
            return fallback

    if decision and decision.action == "inject_assessment":
        label = _instrument_label((decision.selection or {}).get("instrument_id", ""))
        if len(cleaned) < 35 or "가장 먼저" in cleaned or user_message.strip() in cleaned:
            return fallback
        if label.split("(")[0] not in cleaned and "검사" not in cleaned and "질문" not in cleaned:
            return fallback

    if (detect_distress(user_message) or session_has_distress(state, user_message)) and user_message.strip() in cleaned:
        return fallback

    result = cleaned if cleaned else fallback
    last = _last_assistant_message(state)
    if _is_near_duplicate(result, last):
        return _anti_repeat_reply(user_message, state, decision, assessment_response, blocked=result)

    from app.services.mood_assistant import maybe_append_natural_nudge, resolve_mood_context

    ctx = resolve_mood_context(state.user_id)
    result = maybe_append_natural_nudge(result, state, ctx)
    return result


async def _yield_text_with_pacing(text: str, delay: float = 0.028) -> AsyncIterator[str]:
    tokens = re.findall(r"\S+\s*|\n", text)
    for token in tokens:
        yield token
        await asyncio.sleep(delay)


def build_chat_messages(
    state: ChatSessionState,
    user_message: str,
    assessment_response: Optional[Dict[str, Any]] = None,
    preferred_school: Optional[ClinicalSchool] = None,
    decision: Optional[OrchestratorDecision] = None,
    homework_response: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, str]]:
    school = ClinicalSchool(state.preferred_school or ClinicalSchool.ROGERIAN.value)
    distortions = (state.persona_routing or {}).get("detected_distortions") or []
    quant = state.quant_features or extract_chat_quant_features(user_message, state)

    binding = PromptContextWeightBindingFactory(
        school=school,
        psychological_readiness_index=quant["psychological_readiness_index"],
        cognitive_distortions=distortions,
        attachment_matrix_score=quant["attachment_matrix_score"],
        tree_energy_index=quant["tree_energy_index"],
        psychiatric_stress_weight=quant["psychiatric_stress_weight"],
        structural_sign=quant["structural_sign"],
    ).build()

    system_prompt = (
        build_chat_system_prompt(COUNSELOR_NAME)
        + "\n\n"
        + build_persona_directive(school, distortions)
        + "\n\n"
        + binding["system_prompt"]
        + "\n\n"
        + binding["context_block"]
    )

    if state.counseling_phase == "rapport" and state.turn_count <= 2:
        system_prompt += "\n\n이번 턴은 관계 형성·첫 인사에 가깝습니다. 따뜻하게 환영하고, 부담 없이 한 문장만 더 물어보세요."

    system_prompt += "\n\n" + build_phase_prompt(state, user_message)
    system_prompt += build_tarot_system_block(state)
    system_prompt += build_homework_chat_context(state)

    from app.services.daily_routine import build_daily_context_block
    from app.services.mood_assistant import build_mood_mandatory_system_block, resolve_mood_context

    ctx = resolve_mood_context(state.user_id)
    system_prompt += "\n\n" + build_mood_mandatory_system_block(ctx, state)

    daily_block = build_daily_context_block(state.user_id)
    if daily_block:
        system_prompt += "\n\n" + daily_block

    if should_suggest_tarot(state):
        system_prompt += (
            "\n\n내담자가 사례를 정리하는 단계입니다. 대화 흐름이 자연스럽다면 "
            "타로 카드로 마음을 비춰보는 선택을 부드럽게 제안할 수 있습니다. "
            "강요하지 말고, 카드는 점이 아니라 자기 성찰 도구임을 짧게 안내하세요."
        )

    if detect_assessment_request(user_message):
        system_prompt += (
            "\n\n내담자가 검사·상태 확인을 요청했습니다. "
            "'가능하다'고 명확히 답하고, 곧 이어질 짧은 심리검사(스크리닝)를 자연스럽게 안내하세요. "
            "질문을 그대로 반복하거나 '가장 먼저 다루고 싶은 이야기'만 되묻지 마세요."
        )

    if session_has_distress(state, user_message) and not detect_assessment_request(user_message):
        system_prompt += (
            "\n\n내담자가 우울·답답함 등 고통 신호를 보였습니다. "
            "감정을 먼저 반영하고, 필요하면 검사·상담 안내도 자연스럽게 언급하세요."
        )

    if decision and decision.action == "inject_assessment":
        instrument_id = (decision.selection or {}).get("instrument_id", "")
        system_prompt += (
            f"\n\n이번 턴에 {instrument_id} 관련 짧은 검사 카드가 함께 표시됩니다. "
            "상담 멘트에서 검사를 소개하고, 아래 카드에서 답하도록 부드럽게 안내하세요."
        )

    if assessment_response:
        if assessment_response.get("skipped"):
            system_prompt += "\n\n내담자가 확인 질문을 나중으로 미뤘습니다. 억지로 묻지 말고 대화를 이어가세요."
        else:
            system_prompt += (
                "\n\n내담자가 방금 짧은 확인 질문에 답했습니다. "
                "답을 분석하기보다 고마움을 표현하고, 감정 탐색으로 자연스럽게 이어가세요."
            )

    if homework_response:
        if homework_response.get("skipped"):
            system_prompt += "\n\n내담자가 후처리 과제를 나중으로 미뤘습니다. 부담 주지 말고 대화를 이어가세요."
        else:
            system_prompt += (
                "\n\n내담자가 방금 후처리 과제(일기·감정 기록 등)를 작성했습니다. "
                "과제 내용을 짧게 반영하고, 감정을 먼저 수용한 뒤 스스로 돌본 노력을 인정해 주세요. "
                "채점·평가하지 마세요."
            )

    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    messages.extend(state.messages[-14:])
    messages.append({"role": "user", "content": user_message})

    last_assistant = _last_assistant_message(state)
    if last_assistant:
        system_prompt += (
            "\n\n직전 턴과 **같은 문장·같은 질문을 반복하지 마세요**. "
            "내담자의 새 메시지에 맞춰 한 단계 더 깊이 반응하세요."
        )
        messages[0]["content"] = system_prompt

    return messages


async def stream_chat_completion(
    messages: List[Dict[str, str]],
    max_tokens: int,
    client: Any,
    state: ChatSessionState,
    decision: Optional[OrchestratorDecision] = None,
    assessment_response: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[str]:
    user_message = messages[-1]["content"] if messages else ""
    if not client or not getattr(client, "api_key", None):
        async for chunk in _yield_text_with_pacing(
            fallback_reply(user_message, state, decision, assessment_response)
        ):
            yield chunk
        return

    try:
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.82,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta
    except Exception:
        async for chunk in _yield_text_with_pacing(
            fallback_reply(user_message, state, decision, assessment_response)
        ):
            yield chunk


async def run_chat_turn(
    state: ChatSessionState,
    user_message: str,
    client: Any,
    max_tokens: int = 380,
    assessment_response: Optional[Dict[str, Any]] = None,
    homework_response: Optional[Dict[str, Any]] = None,
    stream_fn: Optional[Callable[..., AsyncIterator[str]]] = None,
    preferred_school: Optional[ClinicalSchool] = None,
) -> AsyncIterator[Dict[str, Any]]:
    state.turn_count += 1
    homework_package: Optional[Dict[str, Any]] = None

    explicit_school = preferred_school
    if explicit_school is None and state.preferred_school:
        explicit_school = ClinicalSchool(state.preferred_school)
    routing = route_clinical_persona(user_message, explicit_school, state.messages)
    state.persona_routing = {
        "school": routing["school"].value,
        "mood_state": routing["mood_state"].value,
        "reason": routing["reason"],
        "persona_label": routing["persona_label"],
        "detected_distortions": routing["detected_distortions"],
    }
    state.preferred_school = routing["school"].value
    state.quant_features = extract_chat_quant_features(user_message, state)

    if assessment_response:
        recorded = record_assessment_answer(state, assessment_response)
        yield {"event": "assessment_recorded", "data": recorded}
    elif state.pending_assessment:
        # 새 메시지를 보냈지만 이전 검사에 답하지 않음 → 흐름이 끊기지 않게 해제
        state.pending_assessment = None

    if homework_response:
        recorded = record_homework_submission(
            state,
            homework_response.get("assignment_id", ""),
            homework_response.get("responses") or {},
            skipped=bool(homework_response.get("skipped")),
        )
        yield {"event": "homework_recorded", "data": recorded}

    phase_info = sync_counseling_phase(state, user_message)

    from app.services.mood_assistant import (
        build_assessment_briefing_reply,
        enrich_package_with_mood,
        resolve_mood_context,
    )

    ctx = resolve_mood_context(state.user_id)
    state.phase_notes["today_mood"] = ctx.to_dict()

    if state.counseling_phase == PHASE_ASSESSMENT_BRIEFING and not state.assessment_package_ready:
        package = build_assessment_package(state, user_message)
        package = enrich_package_with_mood(package, ctx, state)
        mark_package_presented(state, package)
        yield {"event": "assessment_package", "data": package}
        briefing = build_assessment_briefing_reply(ctx, package)
        yield {"event": "mood_briefing", "data": {"message": briefing, "mood": ctx.to_dict()}}

    homework_package = maybe_assign_homework(state, user_message)
    if homework_package:
        yield {"event": "homework", "data": homework_package}

    decision = decide_turn(state, user_message, assessment_response=assessment_response, client=client)
    yield {
        "event": "orchestrator",
        "data": {
            "action": decision.action,
            "reason": decision.reason,
            "fatigue": decision.fatigue,
            "counselor_name": COUNSELOR_NAME,
            "selection": decision.selection,
            "persona": state.persona_routing,
            "counseling_phase": phase_info,
        },
    }

    if decision.action == "inject_assessment" and decision.assessment:
        record_assessment_offer(state, decision.assessment)
        yield {"event": "assessment", "data": decision.assessment}

    messages = build_chat_messages(
        state, user_message, assessment_response, preferred_school, decision, homework_response
    )
    streamer = stream_fn or stream_chat_completion
    assistant_chunks: List[str] = []

    skip_llm_briefing = (
        state.counseling_phase == PHASE_ASSESSMENT_BRIEFING
        and state.assessment_package
        and not state.phase_notes.get("assessment_briefing_spoken")
    )

    if skip_llm_briefing:
        briefing = build_assessment_briefing_reply(ctx, state.assessment_package)
        state.phase_notes["assessment_briefing_spoken"] = True
        async for token in _yield_text_with_pacing(briefing):
            assistant_chunks.append(token)
            yield {"event": "token", "data": {"content": token}}
    elif stream_fn:
        async for token in streamer(messages, max_tokens, client, assessment_response):
            assistant_chunks.append(token)
            yield {"event": "token", "data": {"content": token}}
    else:
        async for token in streamer(
            messages, max_tokens, client, state, decision, assessment_response
        ):
            assistant_chunks.append(token)
            yield {"event": "token", "data": {"content": token}}

    assistant_text = enrich_assistant_reply(
        "".join(assistant_chunks).strip(),
        user_message,
        state,
        decision,
        assessment_response,
    )
    state.messages.append({"role": "user", "content": user_message})
    state.messages.append({"role": "assistant", "content": assistant_text})

    profile_delta = build_profile_delta(state)
    profile_delta["persona_routing"] = state.persona_routing
    profile_delta["quant_features"] = state.quant_features
    yield {
        "event": "done",
        "data": {
            "session_id": state.session_id,
            "assistant_message": assistant_text,
            "counselor_name": COUNSELOR_NAME,
            "persona": state.persona_routing,
            "profile_delta": profile_delta,
            "counseling_phase": phase_snapshot(state),
            "suggest_tarot": should_suggest_tarot(state),
            "tarot_blended": state.tarot_blended,
            "homework": homework_package or None,
            "today_mood": ctx.to_dict(),
        },
    }


def format_sse(event: Dict[str, Any]) -> Dict[str, str]:
    return {
        "event": event["event"],
        "data": json.dumps(event["data"], ensure_ascii=False),
    }
