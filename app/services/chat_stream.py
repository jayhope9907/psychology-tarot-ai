from __future__ import annotations

import asyncio
import json
import re
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from app.models.clinical import ClinicalSchool
from app.prompt_config import COUNSELOR_NAME, build_chat_system_prompt, build_human_presence_directive
from app.services.counseling_core_triad import (
    build_core_triad_directive,
    empathic_silence_ms,
    multimodal_tone_hint,
)
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
from app.services.instant_keyword_router import build_instant_reaction_prompt, react_instantly
from app.services.prompt_binding import PromptContextWeightBindingFactory, extract_chat_quant_features

from app.assessments.user_voice import user_instrument_title

INSTRUMENT_LABELS = {
    "phq9": "요즘 마음 기분 들여다보기",
    "gad7": "걱정·불안한 마음 살펴보기",
    "attachment_ecr": "관계·가까움·거리감",
    "isi": "잠·수면 이야기",
    "pss": "스트레스·버거움",
    "micro_emotion": "지금 마음 무게",
    "sct": "문장 이어쓰기 · 마음 글씨",
    "rses": "나 자신을 바라보는 마음",
    "cbt_thought": "자주 드는 생각 패턴",
    "psychodynamic": "반복되는 마음·관계",
    "behavioral": "미루기·피하기·즐거움",
    "htp": "집·나무·사람 상상하기",
    "tarot_reflect": "지금 마음에 닿는 상징",
    "pcl5": "힘든 기억·마음 반응",
}


def _instrument_label(instrument_id: str) -> str:
    return user_instrument_title(instrument_id) or INSTRUMENT_LABELS.get(instrument_id, "마음 상태")


_REPEAT_BANNED_PHRASES = (
    "가장 먼저 나누고",
    "충분히 이해돼",
    "천천히 들려",
    "편한 만큼만 더 들려",
    "한 장면만 짧게",
    "이야기를 나눠 주셔서",
    "이야기해 주셔서",
)


def _normalize_compare(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip().lower())
    return re.sub(r"[^\w\s가-힣]", "", cleaned)


def _char_ngrams(text: str, n: int = 2) -> set[str]:
    normalized = _normalize_compare(text)
    if len(normalized) < n:
        return {normalized} if normalized else set()
    return {normalized[i : i + n] for i in range(len(normalized) - n + 1)}


def _text_similarity(a: str, b: str) -> float:
    left, right = _char_ngrams(a), _char_ngrams(b)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _closing_sentence(text: str) -> str:
    parts = [part.strip() for part in re.split(r"[.!?\n]+", (text or "").strip()) if part.strip()]
    return parts[-1] if parts else ""


def _last_assistant_message(state: ChatSessionState) -> str:
    recent = _recent_assistant_messages(state, 1)
    return recent[0] if recent else ""


def _recent_assistant_messages(state: ChatSessionState, limit: int = 2) -> List[str]:
    found: List[str] = []
    for entry in reversed(state.messages):
        if entry.get("role") != "assistant":
            continue
        content = (entry.get("content") or "").strip()
        if content:
            found.append(content)
        if len(found) >= limit:
            break
    return found


def _is_near_duplicate(candidate: str, previous: str) -> bool:
    if not candidate or not previous:
        return False
    if candidate == previous:
        return True
    shorter, longer = (candidate, previous) if len(candidate) <= len(previous) else (previous, candidate)
    if len(shorter) >= 24 and shorter in longer:
        return True
    if _text_similarity(candidate, previous) >= 0.62:
        return True
    candidate_close = _closing_sentence(candidate)
    previous_close = _closing_sentence(previous)
    if candidate_close and previous_close and len(candidate_close) >= 10:
        if candidate_close == previous_close or _text_similarity(candidate_close, previous_close) >= 0.78:
            return True
    return False


def _repeats_recent_assistant(state: ChatSessionState, candidate: str) -> bool:
    recent = _recent_assistant_messages(state, 3)
    for previous in recent[:2]:
        if _is_near_duplicate(candidate, previous):
            return True
    candidate_close = _closing_sentence(candidate)
    if candidate_close and len(candidate_close) >= 10:
        for previous in recent:
            if _is_near_duplicate(candidate_close, _closing_sentence(previous)):
                return True
    normalized = _normalize_compare(candidate)
    recent_blob = " ".join(_normalize_compare(msg) for msg in recent)
    for phrase in _REPEAT_BANNED_PHRASES:
        if phrase in normalized and phrase in recent_blob:
            return True
    return False


def _seed_variant_index(state: ChatSessionState) -> int:
    if "reply_variant_idx" in state.phase_notes:
        return int(state.phase_notes["reply_variant_idx"] or 0)
    seed_src = f"{state.session_id}:{state.user_id}:{state.turn_count}"
    return sum(ord(ch) for ch in seed_src) % 97


def _pick_variant(state: ChatSessionState, options: List[str]) -> str:
    if not options:
        return ""
    start = _seed_variant_index(state)
    for offset in range(len(options)):
        index = (start + offset) % len(options)
        candidate = options[index]
        if not _repeats_recent_assistant(state, candidate):
            state.phase_notes["reply_variant_idx"] = index + 1
            return candidate
    state.phase_notes["reply_variant_idx"] = start + 1
    return options[start % len(options)]


def build_anti_repeat_directive(state: ChatSessionState) -> str:
    recent = _recent_assistant_messages(state, 2)
    if not recent:
        return ""
    lines = [
        "## 직전 답변 반복 금지",
        "아래 문장·질문과 **같은 표현·같은 마무리 질문**을 쓰지 마세요. "
        "새 장면·감각·관계 한 조각만 짚고 사람답게 이어가세요. "
        "표현만 바꿔 같은 말을 반복하는 챗봇식 재진술은 금지입니다.",
    ]
    for idx, message in enumerate(recent, 1):
        snippet = message[:220] + ("…" if len(message) > 220 else "")
        lines.append(f"- 직전 {idx}: {snippet}")
    return "\n".join(lines)


_CHATBOT_LEAK_PATTERNS = (
    "ai로서",
    "인공지능",
    "챗봇",
    "도와드릴게요",
    "무엇을 도와드릴까요",
    "질문해 주셔서",
    "요약하면",
    "정리해 드리면",
    "다음과 같습니다",
    "세 가지",
    "1.",
    "2.",
    "3.",
)


def _looks_like_chatbot_output(text: str) -> bool:
    lowered = (text or "").strip().lower()
    if not lowered:
        return False
    if lowered.count("\n-") >= 2 or lowered.count("\n•") >= 2:
        return True
    hits = sum(1 for p in _CHATBOT_LEAK_PATTERNS if p in lowered)
    if "1." in text and "2." in text:
        return True
    return hits >= 2


def _dechatbot_reply(user_message: str, state: ChatSessionState) -> str:
    snippet = (user_message or "").strip()
    focus = snippet[:42] if snippet else "지금 마음"
    return (
        f"‘{focus}’ 이야기, 여기서 잠깐 머물러 볼게요. "
        "방금 말씀하신 것 중에 가장 묵직한 한 조각만 먼저 들어보고 싶어요. "
        "어떤 장면이 제일 선명한가요?"
    )


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
        return _pick_variant(
            state,
            [
                "상사와의 그 순간, 어떤 말이나 표정이 특히 마음에 박혔는지 기억나는 게 있을까요?",
                "회사에서 버티기 힘든 요즘, 하루 중 어느 시간대가 특히 버거운지 들려주실 수 있을까요?",
                "자신감이 떨어진다고 하셨는데, 그게 가장 크게 느껴지는 장면은 어떤 상황인가요?",
            ],
        )

    if detect_distress(user_message) or session_has_distress(state, user_message):
        return _pick_variant(
            state,
            [
                "힘드시다는 말, 잘 받았어요. 그때 몸 쪽에서는 어떤 신호가 올라오나요?",
                "말씀해 주신 마음이 반복될 때, 주변에서 무엇이 특히 버거웠나요?",
                "지금 이야기를 이어가려면, 가장 먼저 짚고 싶은 장면 하나만 골라 주실 수 있을까요?",
            ],
        )

    if _is_short_follow_up(user_message):
        return _pick_variant(
            state,
            [
                "네, 이어서 들을게요. 그때 마음속에 떠오른 생각이 있다면 어떤 쪽에 가깝나요?",
                "맞아요, 그 흐름 이어서요. 그 상황에서 몸은 어떻게 반응했는지도 궁금해요.",
                "그렇군요. 그때 특히 남는 감정 하나를 고르면 무엇에 가깝나요?",
            ],
        )

    return _pick_variant(
        state,
        [
            "말씀해 주셔서 고마워요. 방금 이야기 중에서 특히 손이 가는 부분이 어디인가요?",
            "나눠 주신 내용, 차분히 받았어요. 조금 더 구체적인 장면이 떠오르면 들려주세요.",
            "지금 이야기의 핵심이 어디에 있는지 함께 찾아보면 좋겠어요. 어떤 순간이 가장 선명한가요?",
        ],
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

    if _workplace_context(state, user_message) or any(
        kw in user_message for kw in ("직장", "회사", "상사", "업무")
    ):
        return _pick_variant(
            state,
            [
                "직장에서의 그 마음, 잘 전해졌어요. 특히 어떤 장면이 가장 오래 남았나요?",
                "회사 이야기군요. 상사·동료·업무 중 어디가 가장 버거웠는지 들려주실 수 있을까요?",
                "일하면서 자신감이 흔들리는 느낌, 이해돼요. 하루 중 어느 때가 특히 힘든지 궁금해요.",
            ],
        )

    substance_blob = user_message.lower()
    if any(
        kw in substance_blob
        for kw in ("술", "담배", "마약", "중독", "갈망", "재발", "단주", "단약", "금단", "과음")
    ):
        return _pick_variant(
            state,
            [
                "술·습관 이야기를 꺼내 주셔서 고마워요. 최근에 가장 강하게 올라온 갈망은 어떤 순간에 있었나요?",
                "끊으려다 다시 이어진 흐름, 충분히 버거운 일이에요. 그 직전에 어떤 상황·감정이 있었는지 들려주실 수 있을까요?",
                "지금은 비난보다 패턴을 함께 보는 게 좋아요. 평소 트리거(사람·장소·감정) 중 하나만 짚어볼까요?",
            ],
        )

    if state.counseling_phase == "rapport" and not detect_distress(user_message) and not detect_assessment_request(user_message):
        return _pick_variant(
            state,
            [
                "방금 말씀하신 부분에서 특히 마음에 걸리는 장면이 있다면 들려주실 수 있을까요?",
                "나눠 주신 이야기, 차분히 받았어요. 조금 더 구체적인 순간이 떠오르면 이어 주세요.",
                "지금 이야기의 중심이 어디에 있는지 함께 찾아보면 좋겠어요. 어떤 장면이 가장 선명한가요?",
            ],
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

    if (
        state.counseling_phase == "rapport"
        and not is_rapport_complete(state, user_message)
        and not detect_distress(user_message)
        and not detect_assessment_request(user_message)
    ):
        readiness = rapport_readiness(state, user_message)
        missing = readiness["missing"][0] if readiness["missing"] else "지금 마음"
        return _pick_variant(
            state,
            [
                "아직은 검사보다 이야기에 귀 기울이고 싶어요. 편한 만큼만 더 들려주실 수 있을까요?",
                f"{missing.replace('고객의 구체적 이야기를 2회 이상 더 들어주세요', '이야기')}에 대해 조금만 더 알려주시면 도움이 될 것 같아요.",
                "지금 마음을 더 잘 이해하려면, 한 가지 장면만 더 구체적으로 들려주실 수 있을까요?",
            ],
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
            "검사가 쌓일수록 정상 범주인지, 전문 기관 상담을 고려할 여지가 있는지 더 정확히 안내해 드릴 수 있어요. "
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
            "편한 만큼만 선택해 주시면, 정상 범주인지 전문 기관 상담을 고려할 여지가 있는지도 함께 살펴볼 수 있어요."
        )

    if detect_assessment_request(user_message):
        return (
            "네, 검사·상태 확인은 가능해요. "
            "대화 속에서 PHQ·GAD 같은 표준 도구를 짧게 진행하고, "
            "정상 범주인지 전문 기관 상담·추가 평가를 고려할 여지가 있는지 참고 지표로 안내해 드릴게요. "
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
        return _pick_variant(
            state,
            [
                "지금 많이 힘드신 것 같아요. 그 감정이 특히 크게 느껴지는 순간이 있다면 들려주세요.",
                "버거운 마음이 전해져요. 하루 중 어느 때가 특히 힘든지도 함께 나눠 주실 수 있을까요?",
                "힘든 마음, 잘 받았어요. 그때 몸에서는 어떤 신호가 올라오나요?",
            ],
        )

    if "관계" in user_message or "대인" in user_message:
        return (
            "관계 이야기군요. 사람과의 연결에서 오는 기분은 마음 전체에 큰 영향을 주죠. "
            "요즘 관계에서 가장 마음에 걸리는 부분이 무엇인지 들려주실 수 있을까요?"
        )

    return (
        "이야기해 주셔서 고마워요. "
        "방금 나누신 내용 중 조금 더 짚고 싶은 지점이 있다면 어디인지 말씀해 주세요."
    )


def enrich_assistant_reply(
    text: str,
    user_message: str,
    state: ChatSessionState,
    decision: Optional[OrchestratorDecision] = None,
    assessment_response: Optional[Dict[str, Any]] = None,
) -> str:
    """Keep model output when usable; only swap truly empty/off-topic replies."""
    cleaned = (text or "").strip()
    fallback = fallback_reply(user_message, state, decision, assessment_response)

    if not cleaned:
        return fallback

    if detect_assessment_request(user_message):
        if len(cleaned) < 36 and "가능" not in cleaned and "검사" not in cleaned and "체크" not in cleaned:
            return fallback

    result = cleaned
    if _repeats_recent_assistant(state, result):
        return _anti_repeat_reply(user_message, state, decision, assessment_response, blocked=result)
    if _looks_like_chatbot_output(result):
        return _dechatbot_reply(user_message, state)

    from app.services.mood_assistant import maybe_append_natural_nudge, resolve_mood_context

    ctx = resolve_mood_context(state.user_id)
    result = maybe_append_natural_nudge(result, state, ctx)
    return result


def _stream_pacing_delay(default: float = 0.028, *, empathic_boost: float = 1.0) -> float:
    import os

    raw = (os.getenv("CHAT_STREAM_PACING") or "").strip().lower()
    if raw in {"0", "off", "false", "none"}:
        return 0.0
    if os.getenv("PYTEST_CURRENT_TEST"):
        return 0.0
    try:
        base = max(0.0, float(raw)) if raw else default
    except ValueError:
        base = default
    return max(0.0, base * max(0.6, min(2.2, empathic_boost)))


async def _yield_text_with_pacing(
    text: str,
    delay: float | None = None,
    *,
    empathic_boost: float = 1.0,
) -> AsyncIterator[str]:
    pace = _stream_pacing_delay(empathic_boost=empathic_boost) if delay is None else delay
    tokens = re.findall(r"\S+\s*|\n", text)
    for token in tokens:
        yield token
        if pace:
            await asyncio.sleep(pace)


def build_chat_messages(
    state: ChatSessionState,
    user_message: str,
    assessment_response: Optional[Dict[str, Any]] = None,
    preferred_school: Optional[ClinicalSchool] = None,
    decision: Optional[OrchestratorDecision] = None,
    homework_response: Optional[Dict[str, Any]] = None,
    counselor_name: Optional[str] = None,
    style_block: str = "",
    image_data_url: Optional[str] = None,
    image_search_payload: Optional[Dict[str, Any]] = None,
    multimodal_meta: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    name = counselor_name or COUNSELOR_NAME
    try:
        school = ClinicalSchool(state.preferred_school) if state.preferred_school else ClinicalSchool.INTEGRATIVE
    except ValueError:
        school = ClinicalSchool.INTEGRATIVE
    distortions = (state.persona_routing or {}).get("detected_distortions") or []
    quant = state.quant_features or extract_chat_quant_features(user_message, state)

    from app.services.consultation_mode import (
        MODE_FAITH,
        bind_consultation_mode_prompts,
        personal_pattern_prompt_for_mode,
        resolve_consultation_mode,
    )

    consultation_mode = resolve_consultation_mode(
        state.user_id,
        session_mode=getattr(state, "consultation_mode", None),
    )
    state.consultation_mode = consultation_mode

    from app.services.commercial_license_context import resolve_license_context
    from app.services.mode_analyzers import run_mode_specific_analyzer

    lic_ctx = resolve_license_context(state.user_id, session=state)
    analyzer = run_mode_specific_analyzer(
        consultation_mode,
        user_message,
        base_distortions=distortions,
    )
    spiritual_hits: List[str] = list(analyzer.get("spiritualDistortionFlags") or [])
    if analyzer.get("cognitiveDistortionFlags"):
        distortions = list(analyzer["cognitiveDistortionFlags"])
        if state.persona_routing is not None:
            state.persona_routing = dict(state.persona_routing)
            state.persona_routing["detected_distortions"] = distortions
            state.persona_routing["mode_analyzer"] = {
                "analyzerId": analyzer.get("analyzerId"),
                "spiritualDryness": analyzer.get("spiritualDryness"),
                "cbt15Flags": analyzer.get("cbt15Flags"),
            }
            if spiritual_hits:
                state.persona_routing["spiritual_distortions"] = spiritual_hits

    binding = PromptContextWeightBindingFactory(
        school=school,
        psychological_readiness_index=quant["psychological_readiness_index"],
        cognitive_distortions=distortions,
        attachment_matrix_score=quant["attachment_matrix_score"],
        tree_energy_index=quant["tree_energy_index"],
        psychiatric_stress_weight=quant["psychiatric_stress_weight"],
        structural_sign=quant["structural_sign"],
    ).build()

    # Shared presence layer
    system_prompt = (
        build_chat_system_prompt(name)
        + "\n\n"
        + build_human_presence_directive(name)
    )

    # Mode-switched persona / CBT vs faith stack
    if consultation_mode == MODE_FAITH:
        # Empathy first; skip heavy secular CBT triad — faith directive replaces CBT focus.
        system_prompt += (
            "\n\n"
            + bind_consultation_mode_prompts(
                mode=consultation_mode,
                counselor_name=name,
                pattern_analysis=None,  # filled after pattern load below
                spiritual_distortions=spiritual_hits,
            )
        )
        if analyzer.get("promptHintKo"):
            system_prompt += "\n\n## 모드 분석기 힌트\n- " + str(analyzer["promptHintKo"])
    else:
        from app.services.counseling_core_triad import build_core_triad_directive

        system_prompt += (
            "\n\n"
            + build_core_triad_directive(tarot_active=bool(getattr(state, "tarot_handoff", None)))
            + "\n\n"
            + build_persona_directive(school, distortions)
            + "\n\n"
            + bind_consultation_mode_prompts(
                mode=consultation_mode,
                counselor_name=name,
                pattern_analysis=None,
            )
        )
        if analyzer.get("promptHintKo"):
            system_prompt += "\n\n## 모드 분석기 힌트\n- " + str(analyzer["promptHintKo"])

    state.phase_notes["license_context"] = {
        "licenseType": lic_ctx.get("licenseType"),
        "organizationId": lic_ctx.get("organizationId"),
        "b2b": lic_ctx.get("b2b"),
    }

    system_prompt += (
        "\n\n"
        + binding["system_prompt"]
        + "\n\n"
        + binding["context_block"]
    )
    tone_extra = multimodal_tone_hint(multimodal_meta or state.phase_notes.get("multimodal_meta"))
    if tone_extra:
        system_prompt += "\n\n" + tone_extra

    try:
        from app.services.emotional_pattern import analyze_personal_pattern

        # CORE algorithm is mode-agnostic; only prompt narration switches.
        pattern_analysis = analyze_personal_pattern(state.user_id)
        state.phase_notes["personal_emotional_pattern"] = {
            "inEmotionalCrisisVsBaseline": pattern_analysis.get("inEmotionalCrisisVsBaseline"),
            "trend": pattern_analysis.get("trend"),
            "sampleSize": pattern_analysis.get("sampleSize"),
            "topDistortions": pattern_analysis.get("topDistortions"),
            "consultationMode": consultation_mode,
        }
        pattern_block = personal_pattern_prompt_for_mode(pattern_analysis, consultation_mode)
        if pattern_block:
            system_prompt += "\n\n" + pattern_block
    except Exception:
        pass

    raw_instant = (state.persona_routing or {}).get("instant_reaction")
    if raw_instant:
        try:
            from app.services.instant_keyword_router import InstantReaction

            instant = InstantReaction(
                school=school,
                score=float(raw_instant.get("score") or 0),
                reason=str(raw_instant.get("reason") or ""),
                matched_keywords=list(raw_instant.get("matched_keywords") or []),
                school_scores=list(raw_instant.get("school_scores") or []),
                techniques=list(raw_instant.get("techniques") or []),
                features=list(raw_instant.get("features") or []),
                technique_hits=list(raw_instant.get("technique_hits") or []),
            )
            system_prompt += "\n\n" + build_instant_reaction_prompt(instant)
        except Exception:
            system_prompt += "\n\n" + build_instant_reaction_prompt(
                react_instantly(user_message, state.messages)
            )
    else:
        system_prompt += "\n\n" + build_instant_reaction_prompt(
            react_instantly(user_message, state.messages)
        )

    if state.counseling_phase == "rapport" and state.turn_count <= 2:
        system_prompt += (
            "\n\n관계 형성 초반입니다. UI에서 이미 인사했다면 재환영하지 말고, "
            "내담자 이번 말에 구체적으로 반응한 뒤 초점 질문 하나만 이어가세요."
        )

    anti_repeat = build_anti_repeat_directive(state)
    if anti_repeat:
        system_prompt += "\n\n" + anti_repeat

    system_prompt += "\n\n" + build_phase_prompt(state, user_message)
    system_prompt += build_tarot_system_block(state)
    system_prompt += build_homework_chat_context(state)

    from app.services.daily_routine import build_daily_context_block
    from app.services.mood_assistant import build_mood_mandatory_system_block, resolve_mood_context

    ctx = resolve_mood_context(state.user_id)
    system_prompt += "\n\n" + build_mood_mandatory_system_block(ctx, state)
    if style_block:
        system_prompt += "\n\n" + style_block

    from app.services.association_agent import build_association_agent_block

    agent_block = build_association_agent_block(state)
    if agent_block:
        system_prompt += "\n\n" + agent_block

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
            "'가능하다'고 명확히 답하고, 곧 이어질 짧은 마음 체크(스크리닝)를 자연스럽게 안내하세요. "
            "질문을 그대로 반복하거나 '가장 먼저 다루고 싶은 이야기'만 되묻지 마세요."
        )

    if session_has_distress(state, user_message) and not detect_assessment_request(user_message):
        system_prompt += (
            "\n\n내담자가 우울·답답함 등 고통 신호를 보였습니다. "
            "감정을 먼저 반영하고, 필요하면 마음 체크·전문 기관 안내도 자연스럽게 언급하세요."
        )

    from app.services.dream_seed import build_dream_seed

    dream = build_dream_seed(state, user_message)
    if dream.get("active"):
        system_prompt += "\n\n" + dream.get("chat_directive", "")
        if dream.get("acknowledgment"):
            system_prompt += f"\n참고 톤: {dream['acknowledgment']}"

    if decision and decision.action == "inject_assessment":
        instrument_id = (decision.selection or {}).get("instrument_id", "")
        system_prompt += (
            f"\n\n이번 턴에 {instrument_id} 관련 짧은 검사 카드가 함께 표시됩니다. "
            "대화 멘트에서 마음 체크를 소개하고, 아래 카드에서 답하도록 부드럽게 안내하세요."
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

    if image_data_url:
        system_prompt += (
            "\n\n내담자가 사진을 첨부했습니다. 사진에 보이는 장면·분위기·감정을 부드럽게 반영하세요. "
            "진단·병명·의학적 판독은 하지 마세요. 사진이 불러일으키는 마음·기억·감각을 함께 탐색하세요. "
            "사생활·얼굴이 보이면 존중하는 톤을 유지하세요."
        )

    if image_search_payload:
        from app.services.image_search import build_image_search_prompt_block

        system_prompt += build_image_search_prompt_block(image_search_payload)

    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    messages.extend(state.messages[-14:])

    if image_data_url:
        caption = (user_message or "").strip() or "이 사진을 함께 봐 주세요."
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": caption},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            }
        )
    else:
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
    messages: List[Dict[str, Any]],
    max_tokens: int,
    client: Any,
    state: ChatSessionState,
    decision: Optional[OrchestratorDecision] = None,
    assessment_response: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[str]:
    last = messages[-1] if messages else {}
    content = last.get("content") if isinstance(last, dict) else ""
    if isinstance(content, list):
        user_message = " ".join(
            part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"
        ).strip()
    else:
        user_message = content if isinstance(content, str) else ""
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
    image_data_url: Optional[str] = None,
    image_search: bool = False,
    multimodal_meta: Optional[Dict[str, Any]] = None,
    pre_sud: Optional[float] = None,
    post_sud: Optional[float] = None,
    intervention_effectiveness: Optional[float] = None,
    consultation_mode: Optional[str] = None,
) -> AsyncIterator[Dict[str, Any]]:
    from app.services.image_search import (
        extract_search_query,
        search_images,
        validate_image_data_url,
        wants_image_search,
    )
    from app.services.consultation_mode import resolve_consultation_mode

    state.consultation_mode = resolve_consultation_mode(
        state.user_id,
        session_mode=getattr(state, "consultation_mode", None),
        override=consultation_mode,
    )

    if multimodal_meta:
        state.phase_notes["multimodal_meta"] = {
            k: multimodal_meta.get(k)
            for k in ("mood_color", "mood_weather", "voice_cue", "color", "weather")
            if multimodal_meta.get(k)
        }

    if pre_sud is not None or post_sud is not None or intervention_effectiveness is not None:
        ep = dict(state.phase_notes.get("emotional_pattern") or {})
        if pre_sud is not None:
            ep["pre_sud"] = pre_sud
        if post_sud is not None:
            ep["post_sud"] = post_sud
        if intervention_effectiveness is not None:
            ep["intervention_effectiveness"] = intervention_effectiveness
        state.phase_notes["emotional_pattern"] = ep

    distress_early = detect_distress(user_message) or session_has_distress(state, user_message)
    silence_ms = empathic_silence_ms(user_message, distress=distress_early)
    # Client honors ms for empathic silence UX; avoid blocking serverless workers.
    yield {
        "event": "presence_wait",
        "data": {
            "ms": silence_ms,
            "label_ko": "마음쉼터가 조심스럽게 생각을 정리하고 있습니다…",
            "distress": bool(distress_early),
        },
    }

    safe_image = validate_image_data_url(image_data_url)
    image_search_payload: Optional[Dict[str, Any]] = None
    if wants_image_search(user_message, explicit=image_search) and not safe_image:
        query = extract_search_query(user_message)
        image_search_payload = await search_images(query)
        yield {"event": "image_results", "data": image_search_payload}

    transcript_user = user_message
    if safe_image:
        caption = (user_message or "").strip() or "사진을 첨부했어요."
        transcript_user = f"[사진 첨부] {caption}"

    state.turn_count += 1
    homework_package: Optional[Dict[str, Any]] = None

    explicit_school = preferred_school
    if explicit_school is None and state.preferred_school:
        try:
            explicit_school = ClinicalSchool(state.preferred_school)
        except ValueError:
            explicit_school = None

    from app.services.counseling_style import resolve_counseling_style
    from app.services.persistence import get_user_settings
    from app.services.user_agent_algorithm import (
        apply_fingerprint_bias,
        fingerprint_prompt_block,
        get_user_agent_bundle,
        seed_quant_from_fingerprint,
    )

    counselor_default: Optional[ClinicalSchool] = None
    if explicit_school is None:
        style_preview = resolve_counseling_style(get_user_settings(state.user_id))
        primary = (style_preview.get("counselor") or {}).get("primary_school")
        if primary:
            try:
                counselor_default = ClinicalSchool(primary)
            except ValueError:
                counselor_default = None

    agent_bundle = get_user_agent_bundle(state.user_id, refresh_patterns=False)
    fingerprint = agent_bundle.get("agent_fingerprint") or {}
    fingerprint_patterns = agent_bundle.get("patterns") or []

    routing = route_clinical_persona(
        user_message,
        explicit_school,
        state.messages,
        counselor_default_school=counselor_default,
    )
    routing = apply_fingerprint_bias(
        routing,
        fingerprint,
        user_explicit=explicit_school is not None,
    )
    state.persona_routing = {
        "school": routing["school"].value,
        "mood_state": routing["mood_state"].value,
        "reason": routing["reason"],
        "persona_label": routing["persona_label"],
        "detected_distortions": routing["detected_distortions"],
        "fingerprint_bias": bool(routing.get("fingerprint_bias")),
        "algo_id": fingerprint.get("algo_id"),
        "techniques": routing.get("techniques") or [],
        "instant_reaction": routing.get("instant_reaction") or {},
    }
    state.preferred_school = routing["school"].value
    state.quant_features = seed_quant_from_fingerprint(
        extract_chat_quant_features(user_message, state),
        fingerprint,
    )
    state.phase_notes["user_agent"] = {
        "algo_id": fingerprint.get("algo_id"),
        "confidence": fingerprint.get("confidence"),
        "summary": fingerprint.get("algorithm_summary_ko"),
        "patterns": [
            {"id": p.get("pattern_id"), "label": p.get("label_ko"), "confidence": p.get("confidence")}
            for p in fingerprint_patterns[:4]
        ],
    }
    agent_prompt_extra = fingerprint_prompt_block(fingerprint, fingerprint_patterns)
    pattern_analysis = None
    try:
        from app.services.emotional_pattern import analyze_personal_pattern

        # Cached for done payload; prompt injection lives in build_chat_messages.
        pattern_analysis = analyze_personal_pattern(state.user_id)
        state.phase_notes["personal_emotional_pattern"] = {
            "inEmotionalCrisisVsBaseline": pattern_analysis.get("inEmotionalCrisisVsBaseline"),
            "trend": pattern_analysis.get("trend"),
            "sampleSize": pattern_analysis.get("sampleSize"),
            "topDistortions": pattern_analysis.get("topDistortions"),
        }
    except Exception:
        pattern_analysis = None
    try:
        from app.services.gentle_reflection import build_dimensional_profile_snippet, gentle_reflection_system_block

        agent_prompt_extra += "\n\n" + gentle_reflection_system_block(state, user_message)
        dim = build_dimensional_profile_snippet(agent_bundle)
        if dim:
            agent_prompt_extra += "\n\n" + dim
    except Exception:
        pass

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
    from app.services.persistence import get_user_settings
    from app.services.counseling_style import build_style_system_block, resolve_counseling_style
    from app.services.legal_compliance import (
        CRISIS_RESOURCES,
        SERVICE_SCOPE_SUMMARY,
        build_crisis_reply,
        build_legal_system_block,
        detect_crisis,
    )

    ctx = resolve_mood_context(state.user_id)
    style = resolve_counseling_style(get_user_settings(state.user_id))
    counselor_name = style["counselor_name"]
    style_block = (
        build_style_system_block(style)
        + "\n\n"
        + build_legal_system_block()
        + (agent_prompt_extra or "")
    )
    state.phase_notes["counseling_style"] = {
        "counselor_id": style["counselor_id"],
        "counselor_name": counselor_name,
        "texture": style["texture"],
        "tone": style["tone"],
        "voice_preset_id": style["voice_preset_id"],
    }
    state.phase_notes["today_mood"] = ctx.to_dict()

    if detect_crisis(user_message):
        crisis_text = build_crisis_reply()
        state.messages.append({"role": "user", "content": transcript_user})
        state.messages.append({"role": "assistant", "content": crisis_text})
        async for token in _yield_text_with_pacing(crisis_text):
            yield {"event": "token", "data": {"content": token}}
        yield {"event": "crisis", "data": {"detected": True, "resources": CRISIS_RESOURCES}}
        yield {
            "event": "done",
            "data": {
                "session_id": state.session_id,
                "assistant_message": crisis_text,
                "counselor_name": counselor_name,
                "crisis_mode": True,
                "counseling_phase": phase_snapshot(state),
                "today_mood": ctx.to_dict(),
                "legal_notice": SERVICE_SCOPE_SUMMARY,
            },
        }
        return

    if state.counseling_phase == PHASE_ASSESSMENT_BRIEFING and not state.assessment_package_ready:
        from app.services.consumer_access import unlock_session_for_consumer

        unlock_session_for_consumer(state)
        package = build_assessment_package(state, user_message)
        package = enrich_package_with_mood(package, ctx, state)
        package["payment_required"] = False
        package["consumer_open"] = True
        mark_package_presented(state, package)
        # 유저용: 결제 대기 없이 바로 검사 단계로
        state.assessment_paid = True
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
            "counselor_name": counselor_name,
            "selection": decision.selection,
            "persona": state.persona_routing,
            "counseling_phase": phase_info,
            "counseling_style": state.phase_notes.get("counseling_style"),
        },
    }

    if decision.action == "inject_assessment" and decision.assessment:
        record_assessment_offer(state, decision.assessment)
        yield {"event": "assessment", "data": decision.assessment}

    messages = build_chat_messages(
        state,
        user_message,
        assessment_response,
        preferred_school,
        decision,
        homework_response,
        counselor_name=counselor_name,
        style_block=style_block,
        image_data_url=safe_image,
        image_search_payload=image_search_payload,
        multimodal_meta=multimodal_meta,
    )
    streamer = stream_fn or stream_chat_completion
    assistant_chunks: List[str] = []
    empathic_boost = 1.0 + min(1.0, silence_ms / 2400.0)

    skip_llm_briefing = (
        state.counseling_phase == PHASE_ASSESSMENT_BRIEFING
        and state.assessment_package
        and not state.phase_notes.get("assessment_briefing_spoken")
    )

    if skip_llm_briefing:
        briefing = build_assessment_briefing_reply(ctx, state.assessment_package)
        state.phase_notes["assessment_briefing_spoken"] = True
        async for token in _yield_text_with_pacing(briefing, empathic_boost=empathic_boost):
            assistant_chunks.append(token)
            yield {"event": "token", "data": {"content": token}}
    elif stream_fn:
        async for token in streamer(messages, max_tokens, client, assessment_response):
            assistant_chunks.append(token)
            yield {"event": "token", "data": {"content": token}}
            pace = _stream_pacing_delay(empathic_boost=empathic_boost)
            if pace:
                await asyncio.sleep(pace)
    else:
        async for token in streamer(
            messages, max_tokens, client, state, decision, assessment_response
        ):
            assistant_chunks.append(token)
            yield {"event": "token", "data": {"content": token}}
            pace = _stream_pacing_delay(default=0.012, empathic_boost=empathic_boost)
            if pace:
                await asyncio.sleep(pace)

    assistant_text = enrich_assistant_reply(
        "".join(assistant_chunks).strip(),
        user_message,
        state,
        decision,
        assessment_response,
    )
    from app.services.freud_jung_tracker import ensure_psychodynamic_metrics

    assistant_text, psychodynamic_metrics = ensure_psychodynamic_metrics(
        assistant_text,
        user_text=user_message,
    )
    state.phase_notes["psychodynamic_metrics"] = psychodynamic_metrics
    state.messages.append({"role": "user", "content": transcript_user})
    state.messages.append({"role": "assistant", "content": assistant_text})

    profile_delta = build_profile_delta(state)
    profile_delta["persona_routing"] = state.persona_routing
    profile_delta["quant_features"] = state.quant_features
    profile_delta["psychodynamic_metrics"] = psychodynamic_metrics
    done_data: Dict[str, Any] = {
        "session_id": state.session_id,
        "assistant_message": assistant_text,
        "counselor_name": counselor_name,
        "persona": state.persona_routing,
        "profile_delta": profile_delta,
        "counseling_phase": phase_snapshot(state),
        "counseling_style": style,
        "voice_preset": style.get("voice"),
        "suggest_tarot": should_suggest_tarot(state),
        "tarot_blended": state.tarot_blended,
        "homework": homework_package or None,
        "today_mood": ctx.to_dict(),
        "user_agent": state.phase_notes.get("user_agent"),
        "consultationMode": getattr(state, "consultation_mode", None) or "psychology",
        "licenseType": getattr(state, "license_type", None) or "B2C_personal",
        "organizationId": getattr(state, "organization_id", None) or state.org_id,
        "psychodynamic_metrics": psychodynamic_metrics,
    }
    if image_search_payload:
        done_data["image_results"] = image_search_payload
    if safe_image:
        done_data["had_image"] = True

    try:
        from app.services.emotional_pattern import record_pattern_from_chat_session

        pattern_doc = record_pattern_from_chat_session(
            state.user_id,
            state,
            pre_sud=pre_sud,
            post_sud=post_sud,
            intervention_effectiveness=intervention_effectiveness,
        )
        done_data["emotional_pattern"] = {
            "sessionId": pattern_doc.get("sessionId"),
            "sudScores": pattern_doc.get("sudScores"),
            "cognitiveMetrics": pattern_doc.get("cognitiveMetrics"),
            "aiInterventionEffectiveness": pattern_doc.get("aiInterventionEffectiveness"),
        }
        if pattern_analysis:
            done_data["personal_pattern_analysis"] = {
                "inEmotionalCrisisVsBaseline": pattern_analysis.get("inEmotionalCrisisVsBaseline"),
                "trend": pattern_analysis.get("trend"),
                "patternReportKo": pattern_analysis.get("patternReportKo"),
                "topDistortions": pattern_analysis.get("topDistortions"),
            }
    except Exception:
        pass

    yield {"event": "done", "data": done_data}


def format_sse(event: Dict[str, Any]) -> Dict[str, str]:
    return {
        "event": event["event"],
        "data": json.dumps(event["data"], ensure_ascii=False),
    }
