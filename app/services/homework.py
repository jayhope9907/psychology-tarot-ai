from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.services.chat_session import ChatSessionState
from app.services.counseling_phase import PHASE_INTERVENTION, PHASE_TERMINATION

HOMEWORK_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "emotion_journal": {
        "type": "emotion_journal",
        "title_ko": "감정 일기",
        "subtitle_ko": "오늘의 일과 지금 마음을 함께 적어 보세요",
        "instruction_ko": (
            "오늘 있었던 일을 떠올리며, 그때와 지금 느껴지는 감정을 적어 보세요. "
            "판단하지 않아도 괜찮아요. 적는 것만으로도 마음이 정리되는 경우가 많아요."
        ),
        "duration_min": 7,
        "fields": [
            {
                "id": "today_event",
                "label": "오늘 기억에 남는 일",
                "placeholder": "예: 회의에서 제 의견이 잘 전달되지 않은 것 같았어요",
                "input": "textarea",
            },
            {
                "id": "current_emotion",
                "label": "지금 가장 크게 느껴지는 감정",
                "placeholder": "예: 답답함, 서운함, 불안",
                "input": "text",
            },
            {
                "id": "emotion_intensity",
                "label": "감정 강도 (0=없음, 10=매우 강함)",
                "placeholder": "0-10",
                "input": "scale",
                "min": 0,
                "max": 10,
            },
            {
                "id": "self_observation",
                "label": "그 감정을 느끼며 나에게 해주고 싶은 말",
                "placeholder": "예: 오늘도 많이 참았구나, 수고했어",
                "input": "textarea",
            },
        ],
    },
    "thought_record": {
        "type": "thought_record",
        "title_ko": "생각 기록지",
        "subtitle_ko": "자동적 사고를 적고, 조금 더 균형 잡힌 시각 찾기",
        "instruction_ko": (
            "힘들었던 순간의 생각을 그대로 적어 보세요. "
            "그다음 증거와 대안 생각을 적으면 마음이 한 박자 느슨해질 수 있어요."
        ),
        "duration_min": 10,
        "fields": [
            {
                "id": "situation",
                "label": "상황",
                "placeholder": "무슨 일이 있었나요?",
                "input": "textarea",
            },
            {
                "id": "automatic_thought",
                "label": "그때 떠오른 생각",
                "placeholder": "예: 나는 항상 이런 식이야",
                "input": "textarea",
            },
            {
                "id": "evidence_for",
                "label": "그 생각을 뒷받침하는 근거",
                "placeholder": "사실이었던 부분",
                "input": "textarea",
            },
            {
                "id": "evidence_against",
                "label": "반대 근거 · 다른 가능성",
                "placeholder": "놓치기 쉬운 다른 해석",
                "input": "textarea",
            },
            {
                "id": "balanced_thought",
                "label": "조금 더 균형 잡힌 생각",
                "placeholder": "예: 이번엔 힘들었지만, 매번 그런 건 아니야",
                "input": "textarea",
            },
        ],
    },
    "day_review": {
        "type": "day_review",
        "title_ko": "하루 돌아보기",
        "subtitle_ko": "오늘의 나를 부드럽게 바라보기",
        "instruction_ko": (
            "하루를 처음부터 떠올리지 않아도 괜찮아요. "
            "가장 마음에 남은 장면 하나만 골라 적어 보세요."
        ),
        "duration_min": 5,
        "fields": [
            {
                "id": "highlight",
                "label": "오늘의 한 장면",
                "placeholder": "어떤 순간이 가장 선명한가요?",
                "input": "textarea",
            },
            {
                "id": "feeling_then",
                "label": "그때의 감정",
                "placeholder": "예: 긴장, 설렘, 무기력",
                "input": "text",
            },
            {
                "id": "feeling_now",
                "label": "지금 돌아보며 느껴지는 감정",
                "placeholder": "예: 아쉬움, 안도, 그리움",
                "input": "text",
            },
            {
                "id": "learned",
                "label": "오늘의 나에게서 발견한 것",
                "placeholder": "작은 것도 괜찮아요",
                "input": "textarea",
            },
        ],
    },
    "grounding_log": {
        "type": "grounding_log",
        "title_ko": "지금 여기 돌아오기",
        "subtitle_ko": "불안할 때 몸과 감각에 집중하기",
        "instruction_ko": "숨을 고르고, 지금 느껴지는 것을 짧게 적어 보세요.",
        "duration_min": 4,
        "fields": [
            {
                "id": "body_sensation",
                "label": "몸에서 느껴지는 것",
                "placeholder": "예: 어깨가 뻐근함, 가슴이 답답함",
                "input": "text",
            },
            {
                "id": "five_senses",
                "label": "지금 보이거나 들리는 것 3가지",
                "placeholder": "예: 창밖 빛, 키보드 소리, 따뜻한 컵",
                "input": "textarea",
            },
            {
                "id": "after_grounding",
                "label": "적고 나서 달라진 느낌",
                "placeholder": "조금이라도 괜찮아진 점",
                "input": "text",
            },
        ],
    },
    "tarot_reflection": {
        "type": "tarot_reflection",
        "title_ko": "카드 성찰 일기",
        "subtitle_ko": "뽑은 카드와 오늘의 마음 연결하기",
        "instruction_ko": "타로 카드가 비춘 테마를 오늘의 경험과 연결해 적어 보세요.",
        "duration_min": 6,
        "fields": [
            {
                "id": "card_resonance",
                "label": "카드 메시지 중 와닿는 부분",
                "placeholder": "어떤 문장이나 이미지가 남았나요?",
                "input": "textarea",
            },
            {
                "id": "life_link",
                "label": "오늘 겪은 일과 연결지어 보기",
                "placeholder": "카드가 비춘 것과 비슷한 순간",
                "input": "textarea",
            },
            {
                "id": "small_step",
                "label": "내일 시도할 작은 한 걸음",
                "placeholder": "5분 이내로 할 수 있는 것",
                "input": "text",
            },
        ],
    },
}


def _has_workplace_context(state: ChatSessionState) -> bool:
    blob = " ".join(
        [
            state.phase_notes.get("chief_complaint", ""),
            " ".join(state.phase_notes.get("goals") or []),
        ]
    )
    return any(keyword in blob for keyword in ("직장", "회사", "업무", "상사", "동료"))


def _has_distress_context(state: ChatSessionState) -> bool:
    insight = state.clinical_insight or {}
    return float(insight.get("distress_probability") or 0) >= 0.35


def select_homework_types(state: ChatSessionState) -> List[str]:
    school = (state.preferred_school or "ROGERIAN").upper()
    selected: List[str] = []

    if state.tarot_handoff:
        selected.append("tarot_reflection")

    if school == "BECK_CBT":
        selected.extend(["thought_record", "emotion_journal"])
    elif school == "FREUDIAN":
        selected.extend(["day_review", "emotion_journal"])
    else:
        selected.extend(["emotion_journal", "day_review"])

    if _has_distress_context(state) or _has_workplace_context(state):
        if "grounding_log" not in selected:
            selected.append("grounding_log")

    deduped: List[str] = []
    for item in selected:
        if item not in deduped:
            deduped.append(item)

    try:
        from app.services.insights import suggest_homework_intensity

        intensity = suggest_homework_intensity(state.user_id)
        if intensity == "light":
            return deduped[:1]
        if intensity == "gentle":
            return [k for k in deduped if k in ("emotion_journal", "grounding_log", "tarot_reflection")][:1] or deduped[:1]
    except Exception:
        pass
    return deduped[:2]


def _personalize_homework(template_key: str, state: ChatSessionState) -> Dict[str, Any]:
    template = HOMEWORK_TEMPLATES[template_key]
    assignment = {
        "id": f"hw_{uuid4().hex[:10]}",
        "template": template_key,
        **template,
        "assigned_at": datetime.now(timezone.utc).isoformat(),
        "phase": state.counseling_phase,
        "personal_note": "",
    }

    chief = (state.phase_notes.get("chief_complaint") or "").strip()
    goals = state.phase_notes.get("goals") or []
    goal_text = goals[0] if goals else ""

    if chief:
        assignment["personal_note"] = f"오늘 나눈 이야기: {chief[:80]}"
    if goal_text:
        assignment["personal_note"] += f" · 함께 정한 방향: {goal_text[:60]}"

    if template_key == "tarot_reflection" and state.tarot_handoff:
        cards = state.tarot_handoff.get("cards") or []
        if cards:
            names = ", ".join(card.get("name_ko", "") for card in cards[:3])
            assignment["instruction_ko"] = (
                f"뽑으신 카드({names})의 메시지를 떠올리며, "
                "오늘의 경험과 연결해 적어 보세요."
            )

    if _has_workplace_context(state) and template_key == "emotion_journal":
        assignment["fields"] = [
            dict(field) for field in template["fields"]
        ]
        assignment["fields"][0]["placeholder"] = (
            "예: 회의·업무·동료와 있었던 일 중 가장 마음에 남는 순간"
        )

    return assignment


def build_homework_package(state: ChatSessionState, reason: str = "") -> Dict[str, Any]:
    template_keys = select_homework_types(state)
    assignments = [_personalize_homework(key, state) for key in template_keys]
    package = {
        "package_id": f"pkg_{uuid4().hex[:8]}",
        "reason": reason or _default_reason(state),
        "phase": state.counseling_phase,
        "intro_ko": _package_intro(state),
        "assignments": assignments,
        "completion_message_ko": (
            "과제를 마쳐 주셔서 고마워요. 적어 두신 내용은 다음 상담에서 "
            "함께 천천히 살펴볼 수 있어요."
        ),
    }
    state.homework_packages.append(package)
    state.pending_homework = assignments[0] if assignments else None
    state.phase_notes["homework_assigned"] = True
    state.phase_notes["last_homework_package_id"] = package["package_id"]
    return package


def _default_reason(state: ChatSessionState) -> str:
    if state.counseling_phase == PHASE_TERMINATION:
        return "상담 마무리 후처리"
    if state.counseling_phase == PHASE_INTERVENTION:
        return "상담 개입 후 자기돌봄 과제"
    return "상담 후처리"


def _package_intro(state: ChatSessionState) -> str:
    if state.counseling_phase == PHASE_TERMINATION:
        return (
            "오늘 상담을 마무리하며, 일상에서 스스로를 돌볼 수 있는 "
            "짧은 과제를 준비했어요. 부담 없는 것부터 시작해 보세요."
        )
    return (
        "오늘 나눈 이야기를 마음에 남기려면, 짧은 글쓰기가 큰 도움이 될 수 있어요. "
        "아래 과제 중 하나를 골라 적어 보세요."
    )


def should_assign_homework(state: ChatSessionState, user_message: str = "") -> bool:
    phase = state.counseling_phase
    if phase not in {PHASE_INTERVENTION, PHASE_TERMINATION}:
        return False

    if phase == PHASE_TERMINATION:
        last_pkg = state.phase_notes.get("last_homework_package_id")
        termination_pkgs = [
            pkg for pkg in state.homework_packages if pkg.get("phase") == PHASE_TERMINATION
        ]
        return not termination_pkgs

    if phase == PHASE_INTERVENTION:
        intervention_turns = sum(
            1 for pkg in state.homework_packages if pkg.get("phase") == PHASE_INTERVENTION
        )
        start = int(state.phase_notes.get("intervention_start_turn") or state.turn_count)
        elapsed = state.turn_count - start
        if intervention_turns >= 2:
            return False
        if elapsed >= 2 and intervention_turns == 0:
            return True
        if elapsed >= 5 and intervention_turns == 1:
            return True
    return False


def maybe_assign_homework(state: ChatSessionState, user_message: str = "") -> Optional[Dict[str, Any]]:
    if not should_assign_homework(state, user_message):
        return None
    return build_homework_package(state)


def record_homework_submission(
    state: ChatSessionState,
    assignment_id: str,
    responses: Dict[str, Any],
    skipped: bool = False,
) -> Dict[str, Any]:
    entry = {
        "assignment_id": assignment_id,
        "responses": responses,
        "skipped": skipped,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "phase": state.counseling_phase,
    }
    state.homework_completed.append(entry)

    if state.pending_homework and state.pending_homework.get("id") == assignment_id:
        state.pending_homework = None

    summary = _summarize_submission(responses, skipped)
    state.phase_notes["last_homework_summary"] = summary
    return {
        "recorded": True,
        "summary": summary,
        "homework_completed_count": len(state.homework_completed),
    }


def _summarize_submission(responses: Dict[str, Any], skipped: bool) -> str:
    if skipped:
        return "과제는 나중으로 미뤘어요."
    emotion = responses.get("current_emotion") or responses.get("feeling_now") or responses.get("feeling_then")
    event = responses.get("today_event") or responses.get("highlight") or responses.get("situation")
    parts = []
    if emotion:
        parts.append(f"감정: {emotion}")
    if event:
        parts.append(f"상황: {str(event)[:60]}")
    return " · ".join(parts) if parts else "과제를 완료했어요."


def homework_snapshot(state: ChatSessionState) -> Dict[str, Any]:
    return {
        "pending": state.pending_homework,
        "packages": state.homework_packages[-3:],
        "completed_count": len(state.homework_completed),
        "last_summary": state.phase_notes.get("last_homework_summary"),
    }


def build_homework_chat_context(state: ChatSessionState) -> str:
    summary = state.phase_notes.get("last_homework_summary")
    if not summary:
        return ""
    return (
        "\n\n## 최근 과제(후처리) 완료 맥락\n"
        f"내담자가 방금 과제를 수행했습니다: {summary}\n"
        "- 과제 내용을 짧게 반영하고, 감정을 먼저 수용한 뒤 한 가지 더 깊이 탐색하세요.\n"
        "- 과제를 평가·채점하지 말고, 스스로 돌본 노력을 인정해 주세요."
    )
