from __future__ import annotations

import asyncio
import json
import re
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from app.models.clinical import ClinicalSchool
from app.prompt_config import COUNSELOR_NAME, build_chat_system_prompt
from app.services.chat_session import ChatSessionState
from app.services.orchestrator import (
    build_profile_delta,
    decide_turn,
    record_assessment_answer,
    record_assessment_offer,
)
from app.services.persona_router import build_persona_directive, route_clinical_persona
from app.services.prompt_binding import PromptContextWeightBindingFactory, extract_chat_quant_features

DISTRESS_PATTERNS = ("불안", "우울", "스트레스", "초조", "무기력", "상실", "두려움", "긴장", "외로움", "잠")


def _reflect_emotion(user_message: str) -> str:
    normalized = user_message.strip()
    for keyword in DISTRESS_PATTERNS:
        if keyword in normalized:
            return keyword
    return ""


def fallback_reply(user_message: str, assessment_response: Optional[Dict[str, Any]] = None) -> str:
    if assessment_response and assessment_response.get("skipped"):
        return (
            "괜찮아요. 지금은 편한 만큼만 나눠도 충분해요. "
            "방금 이야기해 주신 마음이 더 궁금한데, 어떤 순간이 가장 힘드셨나요?"
        )

    if assessment_response and assessment_response.get("value") is not None:
        return (
            "솔직하게 답해 주셔서 고마워요. 그 답변을 들으니 지금 상태가 조금 더 그려져요. "
            "그 감정이 올라올 때, 보통 어떤 생각이 함께 드시나요?"
        )

    emotion = _reflect_emotion(user_message)
    snippet = user_message.strip()[:60] + ("…" if len(user_message.strip()) > 60 else "")

    if emotion:
        return (
            f"말씀해 주신 내용, 충분히 와닿았어요. {emotion}이(가) 크게 느껴지는 시기인 것 같아요. "
            f"특히 \"{snippet}\"라고 하신 부분이 마음에 남았어요. "
            "그때 몸에서는 어떤 느낌이 드셨는지, 조금만 더 들려주실 수 있을까요?"
        )

    return (
        f"천천히 이야기해 주셔서 고마워요. \"{snippet}\" 부분에서 많은 마음이 느껴졌어요. "
        "지금 이 순간, 가장 먼저 다뤄보고 싶은 이야기가 있다면 무엇인가요?"
    )


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

    if state.turn_count <= 1:
        system_prompt += "\n\n이번 턴은 첫 인사에 가깝습니다. 따뜻하게 환영하고, 부담 없이 한 문장만 더 물어보세요."

    if assessment_response:
        if assessment_response.get("skipped"):
            system_prompt += "\n\n내담자가 확인 질문을 나중으로 미뤘습니다. 억지로 묻지 말고 대화를 이어가세요."
        else:
            system_prompt += (
                "\n\n내담자가 방금 짧은 확인 질문에 답했습니다. "
                "답을 분석하기보다 고마움을 표현하고, 감정 탐색으로 자연스럽게 이어가세요."
            )

    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    messages.extend(state.messages[-14:])
    messages.append({"role": "user", "content": user_message})
    return messages


async def stream_chat_completion(
    messages: List[Dict[str, str]],
    max_tokens: int,
    client: Any,
    assessment_response: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[str]:
    user_message = messages[-1]["content"] if messages else ""
    if not client or not getattr(client, "api_key", None):
        async for chunk in _yield_text_with_pacing(fallback_reply(user_message, assessment_response)):
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
        async for chunk in _yield_text_with_pacing(fallback_reply(user_message, assessment_response)):
            yield chunk


async def run_chat_turn(
    state: ChatSessionState,
    user_message: str,
    client: Any,
    max_tokens: int = 380,
    assessment_response: Optional[Dict[str, Any]] = None,
    stream_fn: Optional[Callable[..., AsyncIterator[str]]] = None,
    preferred_school: Optional[ClinicalSchool] = None,
) -> AsyncIterator[Dict[str, Any]]:
    state.turn_count += 1

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
        },
    }

    if decision.action == "inject_assessment" and decision.assessment:
        record_assessment_offer(state, decision.assessment)
        yield {"event": "assessment", "data": decision.assessment}

    messages = build_chat_messages(state, user_message, assessment_response, preferred_school)
    streamer = stream_fn or stream_chat_completion
    assistant_chunks: List[str] = []
    async for token in streamer(messages, max_tokens, client, assessment_response):
        assistant_chunks.append(token)
        yield {"event": "token", "data": {"content": token}}

    assistant_text = "".join(assistant_chunks).strip()
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
        },
    }


def format_sse(event: Dict[str, Any]) -> Dict[str, str]:
    return {
        "event": event["event"],
        "data": json.dumps(event["data"], ensure_ascii=False),
    }
