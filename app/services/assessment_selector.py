from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.assessments import ALL_INSTRUMENTS, INSTRUMENT_PROFILES, profile_summary
from app.assessments.base import AssessmentItem
from app.services.assessment_battery import boost_battery_coverage_scores
from app.services.chat_session import ChatSessionState


@dataclass
class AssessmentSelection:
    instrument_id: str
    item: AssessmentItem
    confidence: float
    method: str
    rationale: str
    scores: Dict[str, float]


def _conversation_text(state: ChatSessionState, user_message: str) -> str:
    parts = [entry.get("content", "") for entry in state.messages[-6:]]
    parts.append(user_message)
    return "\n".join(part for part in parts if part).lower()


def _available_candidates(state: ChatSessionState) -> Dict[str, AssessmentItem]:
    candidates: Dict[str, AssessmentItem] = {}
    for instrument_id, instrument in ALL_INSTRUMENTS.items():
        answers = state.formal_answers.setdefault(instrument_id, {})
        next_item = instrument.next_item(answers)
        if next_item:
            candidates[instrument_id] = next_item
    return candidates


def _score_instrument(instrument_id: str, text: str) -> float:
    profile = INSTRUMENT_PROFILES.get(instrument_id, {})
    score = 0.0
    for keyword in profile.get("keywords", ()):
        if keyword in text:
            score += 1.2
    for keyword in profile.get("counseling_fit", ()):
        if keyword in text:
            score += 0.8
    return score


def _rule_scores(state: ChatSessionState, user_message: str, candidates: Dict[str, AssessmentItem]) -> Dict[str, float]:
    text = _conversation_text(state, user_message)
    scores = {instrument_id: _score_instrument(instrument_id, text) for instrument_id in candidates}

    for instrument_id, answers in state.formal_answers.items():
        if instrument_id not in candidates:
            continue
        if answers:
            scores[instrument_id] = scores.get(instrument_id, 0.0) + 2.5

    if not any(scores.values()):
        scores["micro_emotion"] = scores.get("micro_emotion", 0.0) + 1.0

    return scores


def _pick_best(scores: Dict[str, float], candidates: Dict[str, AssessmentItem]) -> str:
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return ranked[0][0] if ranked else next(iter(candidates))


def _ai_select_instrument(
    state: ChatSessionState,
    user_message: str,
    candidates: Dict[str, AssessmentItem],
    client: Any,
) -> Optional[AssessmentSelection]:
    if not client or not getattr(client, "api_key", None):
        return None

    catalog = "\n".join(
        f"- {instrument_id}: {profile_summary(instrument_id)}"
        for instrument_id in candidates
    )
    history = "\n".join(
        f"{entry.get('role')}: {entry.get('content')}"
        for entry in state.messages[-8:]
    )

    prompt = (
        "당신은 상담 심리 평가 코디네이터입니다. 내담자의 대화 맥락에 가장 적합한 심리검사 1개를 고르세요.\n"
        f"선택 가능한 검사:\n{catalog}\n\n"
        f"최근 대화:\n{history}\n\n"
        f"현재 메시지: {user_message}\n\n"
        "JSON만 반환하세요: {\"instrument_id\": \"...\", \"confidence\": 0.0~1.0, \"rationale\": \"한국어 1문장\"}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=120,
        )
        payload = json.loads(response.choices[0].message.content or "{}")
        instrument_id = str(payload.get("instrument_id") or "").strip()
        if instrument_id not in candidates:
            return None
        confidence = float(payload.get("confidence") or 0.7)
        rationale = str(payload.get("rationale") or "대화 맥락에 맞는 검사를 선택했습니다.")
        return AssessmentSelection(
            instrument_id=instrument_id,
            item=candidates[instrument_id],
            confidence=round(min(1.0, max(0.0, confidence)), 2),
            method="ai",
            rationale=rationale,
            scores={instrument_id: confidence},
        )
    except Exception:
        return None


def select_best_assessment(
    state: ChatSessionState,
    user_message: str,
    client: Any = None,
) -> Optional[AssessmentSelection]:
    candidates = _available_candidates(state)
    if not candidates:
        return None

    ai_selection = _ai_select_instrument(state, user_message, candidates, client)
    if ai_selection:
        rule_scores = boost_battery_coverage_scores(state, _rule_scores(state, user_message, candidates))
        ai_selection.scores = rule_scores
        return ai_selection

    scores = _rule_scores(state, user_message, candidates)
    scores = boost_battery_coverage_scores(state, scores)
    instrument_id = _pick_best(scores, candidates)
    top_score = scores.get(instrument_id, 0.0)
    confidence = min(0.95, 0.45 + top_score * 0.12)

    rationale_map = {
        "phq9": "우울·무기력 신호가 보여 우울 척도를 확인할게요.",
        "gad7": "불안·걱정 표현이 많아 불안 척도를 확인할게요.",
        "isi": "수면 이야기가 있어 불면 척도를 가볍게 볼게요.",
        "pss": "스트레스가 크게 느껴져 지각 스트레스를 확인할게요.",
        "pcl5": "외상·악몽 관련 표현이 있어 스크리닝할게요.",
        "rses": "자기 평가와 관련된 마음을 살펴볼게요.",
        "attachment_ecr": "관계 패턴을 이해하는 질문을 드릴게요.",
        "cbt_thought": "생각 패턴을 함께 살펴볼게요.",
        "psychodynamic": "반복되는 감정 패턴을 탐색해 볼게요.",
        "behavioral": "행동·회피 패턴을 가볍게 확인할게요.",
        "htp": "상상을 통해 마음을 비춰볼 질문이에요.",
        "tarot_reflect": "상징을 통해 지금 마음을 비춰볼게요.",
        "micro_emotion": "지금 감정 온도를 가볍게 확인할게요.",
    }

    return AssessmentSelection(
        instrument_id=instrument_id,
        item=candidates[instrument_id],
        confidence=round(confidence, 2),
        method="rules",
        rationale=rationale_map.get(instrument_id, "대화 맥락에 맞는 검사를 선택했습니다."),
        scores=scores,
    )
