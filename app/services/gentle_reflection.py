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


def soft_observation_line(state: ChatSessionState, user_message: str = "") -> str:
    """예: 제가 봤을 때는 현재 감정이나 하고 있는 일에 많이 힘들어보이시네요."""
    themes = set(_themes_from_state(state))
    msg = user_message or ""
    if any(k in msg for k in ("힘들", "지쳐", "버거", "우울", "불안", "답답")):
        themes.add("distress")
    if any(k in msg for k in ("관계", "친구", "가족", "연인", "동료", "상사")):
        themes.add("relationship")
    if any(k in msg for k in ("회사", "일", "업무", "야근", "과제")):
        themes.add("work")

    if "relationship" in themes and "work" in themes:
        return (
            "제가 보기에 요즘 하고 계신 일과 사람들 사이 모두에서 "
            "마음이 꽤 쓰이고 계신 것 같아요."
        )
    if "relationship" in themes:
        return (
            "제가 보기에 가까운 관계나 사람들 사이에서 "
            "마음이 조금 무거우신 느낌이 드네요."
        )
    if "work" in themes:
        return (
            "제가 보기에 지금 하고 계신 일이나 역할에서 "
            "많이 힘드신 것처럼 보여요."
        )
    if "distress" in themes or "anxiety" in themes or "depression" in themes:
        return (
            "제가 봤을 때는 현재 감정이나 하고 계신 일에 "
            "많이 힘들어 보이시네요."
        )
    return (
        "지금 나누어 주신 이야기 속에서, 마음이 꽤 애쓰며 버티고 계신 느낌이 있어요."
    )


def soft_followup_question(state: ChatSessionState, focus: Optional[str] = None) -> str:
    """한 번에 하나만 — 설문형 연속 질문 금지."""
    themes = set(_themes_from_state(state))
    focus = focus or (
        "relationship" if "relationship" in themes
        else "mood" if ("distress" in themes or "anxiety" in themes)
        else "either"
    )
    if focus == "relationship":
        return (
            "괜찮으시다면, 요즘 관계에서 가장 크게 느껴지는 한 장면만 "
            "편하게 말씀해 주셔도 좋아요."
        )
    if focus == "mood":
        return (
            "혹시 괜찮다면, 지금 이 순간의 마음 온도만 "
            "한 단어나 짧은 문장으로 남겨 주셔도 충분해요."
        )
    return (
        "요즘 마음과 사람들 사이 중, 조금만 더 이야기하고 싶은 쪽이 있으실까요? "
        "없어도 전혀 괜찮아요."
    )


def gentle_reflection_system_block(state: ChatSessionState, user_message: str = "") -> str:
    obs = soft_observation_line(state, user_message)
    q = soft_followup_question(state)
    return (
        "## [필수] 부담 낮은 감정·관계 탐색\n"
        "- 설문·체크리스트처럼 묻지 마세요. 관찰 → 공감 → 개방형 질문 1개 순서입니다.\n"
        f"- 관찰 예시(자연스럽게 변형): 「{obs}」\n"
        f"- 이어서 쓸 수 있는 부드러운 질문 예: 「{q}」\n"
        "- ‘현재 기분 점수는?’ ‘대인관계는 어떠세요?’처럼 직접·연속 질문 금지.\n"
        "- 답하기 부담되면 건너뛰어도 된다고 한 번 알려 주세요.\n"
        "- 진단·단정·충고 남발 금지. 입체적 이해를 위해 천천히 쌓습니다.\n"
    )


def build_dimensional_profile_snippet(agent_bundle: Optional[Dict[str, Any]]) -> str:
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
    lines.append("- 입체화: 기분·관계·선호를 한 번에 몰아 묻지 말고, 관찰 문장으로 풀어 가세요.")
    return "\n".join(lines)
