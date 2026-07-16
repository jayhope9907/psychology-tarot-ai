"""Stress management protocol + reflective replies (non-diagnostic)."""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.chat_session import ChatSessionState
from app.services.clinical_adaptor import normalize_clinical_setup

STRESS_TRIGGER_KEYWORDS = (
    "스트레스",
    "긴장",
    "초조",
    "압박",
    "과부하",
    "빡빡",
    "번아웃",
    "burnout",
    "압박감",
    "긴장감",
)

PROTOCOL_ID = "stress_3min_reset"
PROTOCOL_VERSION = "1.0"


def _text_includes_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = (text or "").lower()
    return any(k in (text or "") or k.lower() in lowered for k in keywords)


def should_trigger_stress_management(user_message: str) -> bool:
    return _text_includes_any(user_message, STRESS_TRIGGER_KEYWORDS)


def build_stress_management_plan(
    *,
    clinical_setup: Optional[Dict[str, Any]] = None,
    pre_sud: Optional[float] = None,
) -> Dict[str, Any]:
    setup = normalize_clinical_setup(
        resistance_level=(clinical_setup or {}).get("resistance_level"),
        sensory_impairment_deaf=(clinical_setup or {}).get("sensory_impairment_deaf"),
        cognitive_level=(clinical_setup or {}).get("cognitive_level"),
    )
    steps = [
        {"id": "breath", "label_ko": "호흡 3번", "duration_sec": 45},
        {"id": "senses", "label_ko": "감각 5초", "duration_sec": 30},
        {"id": "micro_action", "label_ko": "작은 행동 1가지", "duration_sec": 105},
    ]
    return {
        "protocolId": PROTOCOL_ID,
        "protocolVersion": PROTOCOL_VERSION,
        "titleKo": "스트레스 3분 리셋",
        "durationMin": 3,
        "homeworkType": "grounding_log",
        "steps": steps,
        "clinicalAdaptiveSetup": setup,
        "preSud": pre_sud,
        "non_diagnostic": True,
    }


def build_stress_management_reply(
    state: ChatSessionState,
    user_message: str,
    *,
    clinical_setup: Optional[Dict[str, Any]] = None,
    pre_sud: Optional[float] = None,
) -> str:
    setup = normalize_clinical_setup(
        resistance_level=(clinical_setup or {}).get("resistance_level")
        or getattr(state, "resistance_level", None),
        sensory_impairment_deaf=(clinical_setup or {}).get("sensory_impairment_deaf")
        if clinical_setup is not None
        else getattr(state, "sensory_impairment_deaf", False),
        cognitive_level=(clinical_setup or {}).get("cognitive_level")
        or getattr(state, "cognitive_level", None),
    )
    focus = (user_message or "").strip()[:36]
    simple = setup.get("cognitive_level") == "SIMPLE_EASY"
    deaf = bool(setup.get("sensory_impairment_deaf"))
    high_resistance = setup.get("resistance_level") == "HIGH"

    if simple:
        intro = (
            f"‘{focus}’ 말씀, 스트레스가 크게 느껴져요. "
            "지금 3분만 같이 쉬어 볼까요?"
        )
        body = (
            "1) 숨 3번 천천히 내쉬기\n"
            "2) 눈에 보이는 것 1가지 보기\n"
            "3) 1~2분 안에 할 수 있는 작은 일 1가지 고르기"
        )
        choice = (
            "원하시면 지금 바로 해볼까요, 아니면 나중에 할까요?"
            if high_resistance
            else "지금 바로 해볼까요?"
        )
        suffix = " 🌬️ 호흡 · 👀 보기 · ✍️ 한 가지" if deaf else ""
        return f"{intro}\n\n{body}\n\n{choice}{suffix}"

    intro = (
        f"‘{focus}’처럼 스트레스가 선명하게 전해져요. "
        "지금은 길게 풀기보다, 3분 ‘리셋’으로 몸과 마음을 잠깐 정리해 볼 수 있어요."
    )
    body = (
        "① 호흡 3번 — 숨을 천천히 내쉬며 어깨·턱을 한 번 풀어 보세요.\n"
        "② 감각 5초 — 보이는 것, 들리는 것, 몸감각 중 하나에 잠깐 집중해 보세요.\n"
        "③ 작은 행동 1가지 — 1~2분 안에 할 수 있는 가장 작은 일 하나만 정해 보세요."
    )
    if pre_sud is not None:
        body += f"\n(지금 힘듦 {pre_sud}/10으로 표시해 주셨네요. 끝나고 다시 한 번 느보면 좋아요.)"

    if high_resistance:
        choice = (
            "지금 바로 같이 해볼지, 나중에 숙제로 남길지 선택하실 수 있어요. "
            "어느 쪽이 더 편하신가요?"
        )
    else:
        choice = "원하시면 아래 ‘스트레스 3분 리셋’ 숙제로 이어서 기록해 보셔도 좋아요."

    suffix = "\n🙂 안정 · 🌬️ 호흡 · ✍️ 한 줄 기록" if deaf else ""
    return f"{intro}\n\n{body}\n\n{choice}{suffix}"
