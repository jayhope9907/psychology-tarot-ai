"""부담 낮은 감정·대인관계 반영 — 설문처럼 묻지 않고 관찰로 풀어 주기."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.chat_session import ChatSessionState


def _themes_from_state(state: ChatSessionState) -> List[str]:
    themes: List[str] = []
    try:
        from app.services.user_agent_algorithm import extract_message_themes

        blob = " ".join(
            (m.get("content") or "")
            for m in (state.messages or [])[-8:]
            if m.get("role") == "user"
        )
        themes.extend(extract_message_themes(blob))
    except Exception:
        pass
    insight = state.clinical_insight or {}
    if float(insight.get("distress_probability") or 0) >= 0.4:
        themes.append("distress")
    return themes


def soft_observation_focus(state: ChatSessionState, user_message: str = "") -> str:
    """Return focus label only — never a copy-paste Korean sentence for the model."""
    themes = set(_themes_from_state(state))
    msg = user_message or ""
    if any(k in msg for k in ("힘들", "지쳐", "버거", "우울", "불안", "답답")):
        themes.add("distress")
    if any(k in msg for k in ("관계", "친구", "가족", "연인", "동료", "상사")):
        themes.add("relationship")
    if any(k in msg for k in ("회사", "일", "업무", "야근", "과제", "직장")):
        themes.add("work")

    if "relationship" in themes and "work" in themes:
        return "work_and_relationships"
    if "relationship" in themes:
        return "relationships"
    if "work" in themes:
        return "work_role"
    if "distress" in themes or "anxiety" in themes or "depression" in themes:
        return "current_distress"
    return "present_experience"


# Keep old names for callers that expect strings, but avoid teaching fixed phrases.
def soft_observation_line(state: ChatSessionState, user_message: str = "") -> str:
    return soft_observation_focus(state, user_message)


def soft_followup_question(state: ChatSessionState, focus: Optional[str] = None) -> str:
    return focus or soft_observation_focus(state)


def gentle_reflection_system_block(state: ChatSessionState, user_message: str = "") -> str:
    focus = soft_observation_focus(state, user_message)
    return (
        "## [필수] 전문상담사식 감정·맥락 탐색\n"
        "- 설문·체크리스트처럼 묻지 마세요. 순서: 구체 반영 → 초점 1개 탐색.\n"
        f"- 이번 턴 초점 힌트(문장으로 그대로 쓰지 말 것): {focus}\n"
        "- 내담자가 방금 쓴 표현·상황을 자기 말로 바꿔 반영하고, 직전 턴과 다른 질문을 하세요.\n"
        "- ‘현재 기분 점수는?’ ‘대인관계는 어떠세요?’처럼 직접·연속 질문 금지.\n"
        "- 고정 멘트 금지: 「충분히 이해돼요」「가장 먼저 나누고 싶은 마음」 등.\n"
        "- 진단·단정·훈계 금지. 부담되면 건너뛰어도 된다고 짧게만 안내.\n"
    )


def build_anonymous_profile_snippet(agent_bundle: Optional[Dict[str, Any]]) -> str:
    if not agent_bundle:
        return ""
    fp = agent_bundle.get("agent_fingerprint") or {}
    psych = fp.get("psychometric_profile") or {}
    mbti = psych.get("mbti") or {}
    lines = ["## 유저 입체 프로필 (자기성찰·비진단)"]
    if mbti.get("type_code_hint") and "?" not in mbti.get("type_code_hint", "????"):
        lines.append(f"- 선호 경향 힌트(MBTI 교육용): {mbti.get('type_code_hint')}")
    signals = psych.get("abnormal_signals") or {}
    elevated = [k for k, v in signals.items() if isinstance(v, dict) and v.get("severity_hint") == "elevated"]
    if elevated:
        lines.append("- 탐색 신호가 조금 높은 영역(교육용): " + ", ".join(elevated[:4]))
        lines.append("- 위 신호는 진단이 아닙니다. 부드럽게 확인만 하세요.")
    themes = fp.get("theme_hist") or {}
    top_themes = sorted(themes.items(), key=lambda x: -float(x[1]))[:3]
    if top_themes:
        lines.append("- 반복 테마: " + ", ".join(t for t, _ in top_themes))
    if len(lines) == 1:
        return ""
    lines.append("- 입체화: 기분·관계·선호를 한 번에 몰아 묻지 말고, 이번 메시지에 맞게 반응하세요.")
    return "\n".join(lines)
