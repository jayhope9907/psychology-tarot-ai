from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.assessment_battery import sync_session_battery
from app.services.rapport_profiling import is_rapport_complete, rapport_phase_prompt, rapport_readiness, update_client_profile
from app.services.chat_session import ChatSessionState
from app.services.fatigue_manager import (
    detect_assessment_request,
    detect_counseling_request,
    detect_distress,
    session_has_distress,
)

PHASE_RAPPORT = "rapport"
PHASE_ASSESSMENT_BRIEFING = "assessment_briefing"
PHASE_ASSESSMENT = "assessment"
PHASE_CONCEPTUALIZATION = "conceptualization"
PHASE_INTERVENTION = "intervention"
PHASE_TERMINATION = "termination"

PHASE_ORDER: tuple[str, ...] = (
    PHASE_RAPPORT,
    PHASE_ASSESSMENT_BRIEFING,
    PHASE_ASSESSMENT,
    PHASE_CONCEPTUALIZATION,
    PHASE_INTERVENTION,
    PHASE_TERMINATION,
)

PHASE_LABELS_KO: Dict[str, str] = {
    PHASE_RAPPORT: "관계 형성",
    PHASE_ASSESSMENT_BRIEFING: "검사 안내",
    PHASE_ASSESSMENT: "문제 평가·탐색",
    PHASE_CONCEPTUALIZATION: "사례 개념화",
    PHASE_INTERVENTION: "상담 개입",
    PHASE_TERMINATION: "상담 종결",
}

PHASE_DESCRIPTIONS_KO: Dict[str, str] = {
    PHASE_RAPPORT: "신뢰·안전감을 만들고 상담의 틀(비밀·속도·목표)을 안내합니다.",
    PHASE_ASSESSMENT_BRIEFING: "주호소에 맞는 마음 확인 방법을 안내하고, 부담 없이 탐색을 이어갑니다.",
    PHASE_ASSESSMENT: "주호소와 현재 상태를 듣고, 짧은 심리검사로 객관적 단서를 모읍니다.",
    PHASE_CONCEPTUALIZATION: "수집된 정보로 패턴·신념·경험을 연결하고 상담 목표를 구체화합니다.",
    PHASE_INTERVENTION: "CBT·통찰 등 기법으로 목표 달성을 돕고 작은 변화를 시도합니다.",
    PHASE_TERMINATION: "변화를 정리하고, 일상에서 스스로 돌볼 수 있도록 마무리합니다.",
}

TERMINATION_KEYWORDS = (
    "그만",
    "충분",
    "고마워",
    "고맙",
    "끝낼",
    "마무리",
    "종결",
    "종료",
    "나아졌",
    "괜찮아졌",
    "여기까지",
    "오늘은 이 정도",
    "그만둘",
)

INTERVENTION_READY_KEYWORDS = (
    "어떻게",
    "방법",
    "해결",
    "실천",
    "연습",
    "습관",
    "대처",
    "바꾸",
    "개선",
    "도와",
)


def phase_label(phase: str) -> str:
    return PHASE_LABELS_KO.get(phase, PHASE_LABELS_KO[PHASE_RAPPORT])


def phase_index(phase: str) -> int:
    ui_index = {
        PHASE_RAPPORT: 0,
        PHASE_ASSESSMENT_BRIEFING: 1,
        PHASE_ASSESSMENT: 1,
        PHASE_CONCEPTUALIZATION: 2,
        PHASE_INTERVENTION: 3,
        PHASE_TERMINATION: 4,
    }
    return ui_index.get(phase, 0)


def detect_termination_signal(user_message: str) -> bool:
    text = (user_message or "").lower().strip()
    return any(keyword in text for keyword in TERMINATION_KEYWORDS)


def detect_intervention_ready(user_message: str) -> bool:
    text = (user_message or "").lower().strip()
    return any(keyword in text for keyword in INTERVENTION_READY_KEYWORDS)


def _record_chief_complaint(state: ChatSessionState, user_message: str) -> None:
    notes = state.phase_notes
    if notes.get("chief_complaint"):
        return
    cleaned = (user_message or "").strip()
    if len(cleaned) < 8 and not detect_distress(cleaned):
        return
    notes["chief_complaint"] = cleaned[:240]


def _infer_goals(state: ChatSessionState) -> List[str]:
    insight = state.clinical_insight or {}
    chief = state.phase_notes.get("chief_complaint") or ""
    goals: List[str] = []
    if "우울" in chief or any(
        domain.get("domain_id") == "depression"
        for domain in (insight.get("domain_findings") or [])
        if isinstance(domain, dict)
    ):
        goals.append("우울·무기력 감소와 일상 리듬 회복")
    if "불안" in chief or "답답" in chief:
        goals.append("불안·답답함 완화와 마음 안정")
    if "관계" in chief or "대인" in chief:
        goals.append("관계에서의 감정 이해와 소통")
    if not goals:
        goals.append("지금 가장 힘든 마음을 조금씩 덜어내기")
    return goals[:3]


def _battery_completion(state: ChatSessionState) -> float:
    battery = state.battery_coverage or sync_session_battery(state)
    return float(battery.get("overall_completion_rate") or 0.0)


def _insight_confidence(state: ChatSessionState) -> float:
    insight = state.clinical_insight or {}
    return float(insight.get("confidence") or 0.0)


def _advance_phase(state: ChatSessionState, user_message: str) -> None:
    current = state.counseling_phase
    if current not in PHASE_ORDER:
        current = PHASE_RAPPORT
        state.counseling_phase = current

    if detect_termination_signal(user_message):
        state.counseling_phase = PHASE_TERMINATION
        return

    if current == PHASE_TERMINATION:
        if detect_distress(user_message) or detect_counseling_request(user_message):
            state.counseling_phase = PHASE_INTERVENTION
        return

    if current == PHASE_RAPPORT:
        if is_rapport_complete(state, user_message):
            state.counseling_phase = PHASE_ASSESSMENT_BRIEFING
        return

    if current == PHASE_ASSESSMENT_BRIEFING:
        if state.assessment_paid:
            state.counseling_phase = PHASE_ASSESSMENT
        return

    if current == PHASE_ASSESSMENT:
        completion = _battery_completion(state)
        if state.assessments_completed >= 2 and state.turn_count >= 5:
            state.counseling_phase = PHASE_CONCEPTUALIZATION
        elif (
            completion >= 0.22
            and state.assessments_completed >= 1
            and state.turn_count >= 7
        ):
            state.counseling_phase = PHASE_CONCEPTUALIZATION
        return

    if current == PHASE_CONCEPTUALIZATION:
        if (
            _insight_confidence(state) >= 0.28
            or state.turn_count >= 9
            or detect_intervention_ready(user_message)
        ):
            state.counseling_phase = PHASE_INTERVENTION
            if not state.phase_notes.get("goals"):
                state.phase_notes["goals"] = _infer_goals(state)
            if "intervention_start_turn" not in state.phase_notes:
                state.phase_notes["intervention_start_turn"] = state.turn_count
        return

    if current == PHASE_INTERVENTION:
        if state.turn_count >= 20 or detect_termination_signal(user_message):
            state.counseling_phase = PHASE_TERMINATION


def sync_counseling_phase(state: ChatSessionState, user_message: str = "") -> Dict[str, Any]:
    previous = state.counseling_phase
    _record_chief_complaint(state, user_message)
    update_client_profile(state, user_message)
    _advance_phase(state, user_message)

    if state.counseling_phase != previous:
        if not state.phase_history or state.phase_history[-1] != state.counseling_phase:
            state.phase_history.append(state.counseling_phase)

    return phase_snapshot(state, user_message)


def phase_snapshot(state: ChatSessionState, user_message: str = "") -> Dict[str, Any]:
    phase = state.counseling_phase
    rapport = rapport_readiness(state, user_message) if phase == PHASE_RAPPORT else None
    return {
        "phase": phase,
        "phase_label": phase_label(phase),
        "phase_description": _phase_description(phase, rapport),
        "phase_index": phase_index(phase),
        "phase_total": 5,
        "chief_complaint": state.phase_notes.get("chief_complaint"),
        "goals": state.phase_notes.get("goals") or [],
        "history": list(state.phase_history),
        "assessment_paid": state.assessment_paid,
        "assessment_package_ready": state.assessment_package_ready,
        "rapport_readiness": rapport,
        "client_profile": state.phase_notes.get("client_profile"),
    }


def _phase_description(phase: str, rapport: Dict[str, Any] | None) -> str:
    if phase == PHASE_RAPPORT and rapport:
        pct = int(rapport["score"] * 100)
        if rapport["ready"]:
            return f"고객 파악 완료({pct}%). 검사 안내를 준비합니다."
        return f"신뢰 형성 중 · 고객 파악 {pct}% (충분히 파악된 뒤 검사 안내)"
    return PHASE_DESCRIPTIONS_KO.get(phase, "")


def assessments_unlocked(state: ChatSessionState) -> bool:
    try:
        from app.services.consumer_access import consumer_open

        if consumer_open():
            return True
    except Exception:
        pass
    return bool(state.assessment_paid)


def phase_allows_assessment(state: ChatSessionState, user_message: str) -> bool:
    if not assessments_unlocked(state):
        return False

    phase = state.counseling_phase

    if detect_assessment_request(user_message):
        return phase in {
            PHASE_ASSESSMENT,
            PHASE_ASSESSMENT_BRIEFING,
            PHASE_CONCEPTUALIZATION,
            PHASE_INTERVENTION,
            PHASE_TERMINATION,
        }

    if phase == PHASE_RAPPORT:
        return False

    if phase == PHASE_ASSESSMENT_BRIEFING:
        return False

    if phase == PHASE_ASSESSMENT:
        return True

    if phase == PHASE_CONCEPTUALIZATION:
        return detect_distress(user_message) or _battery_completion(state) < 0.15

    if phase == PHASE_INTERVENTION:
        return detect_assessment_request(user_message)

    if phase == PHASE_TERMINATION:
        return detect_assessment_request(user_message)

    return state.turn_count >= 2


def build_phase_prompt(state: ChatSessionState, user_message: str = "") -> str:
    phase = state.counseling_phase
    chief = state.phase_notes.get("chief_complaint") or "아직 정리 중"
    goals = state.phase_notes.get("goals") or []

    if phase == PHASE_RAPPORT:
        return rapport_phase_prompt(state, user_message)

    if phase == PHASE_ASSESSMENT_BRIEFING:
        return (
            "## 현재 상담 단계: 검사 안내·케이스 분류·결제\n"
            f"- 주호소(참고): {chief}\n"
            "- 라포 형성 이후, 대화 기반 **고객 케이스 초기 분류**와 **스크리닝 참고 확률**이 카드로 표시됩니다.\n"
            "- 진단명을 단정하지 말고, '~ 스크리닝 해당 가능성', '참고 확률'로 안내하세요.\n"
            "- 검사를 통해 **그릴 수 있는 미래**(회복·방향)와 **지켜낼 수 있는 것**(악화·만성화 방어)을 짧게 연결하세요.\n"
            "- 결제 전 실제 검사 질문은 하지 말고, 아래 카드 검토를 자연스럽게 권하세요."
        )

    if phase == PHASE_ASSESSMENT:
        return (
            "## 현재 상담 단계: 문제 평가·탐색 (중기 초)\n"
            f"- 주호소(참고): {chief}\n"
            "- 내담자가 가장 힘든 부분을 경청하고, 감정·상황·몸 감각을 함께 탐색하세요.\n"
            "- 곧 이어질 짧은 심리검사(PHQ·GAD 등)는 진단이 아니라 참고용 스크리닝임을 자연스럽게 안내하세요.\n"
            "- 검사를 요청하면 반드시 가능하다고 답하세요."
        )

    if phase == PHASE_CONCEPTUALIZATION:
        return (
            "## 현재 상담 단계: 사례 개념화 (중기)\n"
            f"- 주호소(참고): {chief}\n"
            "- 지금까지 나눈 이야기와 검사 단서를 바탕으로, 증상 이면의 패턴·신념·경험을 조심스럽게 연결해 보세요.\n"
            "- '지도를 그린다'는 느낌으로, 내담자와 함께 이해를 정리하고 상담 목표를 구체화하세요.\n"
            "- 단정적 해석은 피하고, '혹시 ~와 연결될까요?'처럼 탐색형으로 말하세요."
        )

    if phase == PHASE_INTERVENTION:
        goal_text = ", ".join(goals) if goals else "지금 가장 힘든 마음 완화"
        return (
            "## 현재 상담 단계: 상담 개입·실행 (중기 심화)\n"
            f"- 협의된 목표(참고): {goal_text}\n"
            "- CBT(생각·행동 점검), 통찰(반복 패턴), 행동 실험 등 1가지 기법만 짧게 제안하세요.\n"
            "- 오늘 당장 시도할 수 있는 작은 한 걸음을 함께 정하세요.\n"
            "- 새 검사보다 실행·연습·감정 처리에 집중하세요."
        )

    return (
        "## 현재 상담 단계: 상담 종결 (후기)\n"
        "- 그동안의 대화·변화를 따뜻하게 요약하고, 내담자의 노력을 지지하세요.\n"
        "- 앞으로 스스로 돌볼 수 있는 유지·예방 방법(리듬, 연락처, 자기 돌봄)을 1~2가지로 정리하세요.\n"
        "- 필요하면 언제든 다시 찾아와도 된다고 안내하고, 부드럽게 마무리하세요."
    )
