"""일·돈 현실 인정 + 꿈 심기(동기·미래 상상) — 사용자 공감 프레이밍."""
from __future__ import annotations

from typing import Any, Dict, List

from app.services.assessment_selector import _conversation_text
from app.services.chat_session import ChatSessionState

WORK_MONEY_KEYWORDS = (
    "돈", "월급", "연봉", "생계", "생활비", "알바", "아르바이트", "빚", "대출",
    "월세", "전세", "등록금", "학자금", "용돈", "수입", "벌", "벌어", "경제",
    "가난", "부족", "쪼들", "쫓기", "생활", "먹고살",
)

WORK_CONTEXT_KEYWORDS = (
    "직장", "회사", "업무", "일", "출근", "퇴근", "상사", "동료", "야근",
    "번아웃", "burnout", "퇴사", "이직", "실업", "취업", "구직", "면접",
    "프리랜서", "창업", "사업",
)

DREAM_KEYWORDS = (
    "꿈", "하고 싶", "원하", "희망", "미래", "목표", "바라", "이루",
    "성장", "변화", "새로운", "도전",
)

DREAM_PROMPT_POOL: List[str] = [
    "돈 걱정이 조금 줄어든다면, 가장 먼저 하고 싶은 일은 무엇인가요?",
    "3년 뒤 아침 — 어떤 하루로 시작하면 마음이 편할까요?",
    "지금 하는 일 속에서, 이미 키워지고 있는 작은 꿈은 없을까요?",
    "어릴 때 '커서 이렇게 살고 싶다'고 상상했던 모습이 있나요?",
    "월급날이 아니어도, 기분이 가벼워지는 순간은 언제인가요?",
]

BRIDGE_LINES: List[str] = [
    "대부분의 사람은 생활·돈 때문에 일해요. 그건 부끄러운 이유가 아니에요.",
    "생계를 위한 일과 마음의 꿈은 동시에 존재할 수 있어요.",
    "지금 버티는 하루도, 꿈을 위한 한 걸음일 수 있어요.",
    "돈 때문에 선택한 길 위에서도, 작은 꿈은 자랄 수 있어요.",
]

MICRO_SEEDS: List[Dict[str, str]] = [
    {"seed": "이번 주, 꿈과 5분만 연결되는 작은 행동 하나", "why": "거대한 목표보다 작은 씨앗이 마음을 살려요"},
    {"seed": "월급의 아주 작은 몫을 '미래의 나' 통장에", "why": "생계와 꿈 사이 다리를 놓는 ritual"},
    {"seed": "퇴근 후 10분, 꿈 관련 글·그림·노래만 허용", "why": "의미 없는 하루 속 의미 구역 만들기"},
    {"seed": "지금 일에서 배우는 것 1가지 적기", "why": "당장의 돈 + 나중의 성장을 동시에 보기"},
]


def _signal_strength(text: str) -> Dict[str, float]:
    blob = (text or "").lower()
    work_money = sum(1.4 for kw in WORK_MONEY_KEYWORDS if kw in blob)
    work_ctx = sum(1.0 for kw in WORK_CONTEXT_KEYWORDS if kw in blob)
    dream = sum(1.0 for kw in DREAM_KEYWORDS if kw in blob)
    total = work_money + work_ctx + dream
    if total <= 0:
        return {"work_money": 0.0, "work_context": 0.0, "dream": 0.0, "combined": 0.0}
    combined = min(1.0, (work_money * 0.45 + work_ctx * 0.35 + dream * 0.2) / 4.0)
    return {
        "work_money": round(min(1.0, work_money / 3.0), 2),
        "work_context": round(min(1.0, work_ctx / 3.0), 2),
        "dream": round(min(1.0, dream / 2.0), 2),
        "combined": round(combined, 2),
    }


def build_dream_seed(state: ChatSessionState, user_message: str = "") -> Dict[str, Any]:
    """대화·주호소에서 일·돈·꿈 신호를 읽고 꿈 심기 블록 생성."""
    text = _conversation_text(state, user_message)
    chief = (state.phase_notes.get("chief_complaint") or "").lower()
    combined = f"{text}\n{chief}"
    signals = _signal_strength(combined)

    # 기본: 대부분 사용자에게 은은히 적용 (combined 낮아도 universal ack)
    active = signals["combined"] >= 0.12 or signals["work_money"] >= 0.2 or signals["work_context"] >= 0.25
    universal = True  # "대부분 돈 때문에 일한다"는 보편 프레이밍

    prompts = list(DREAM_PROMPT_POOL[:3])
    if signals["dream"] >= 0.3:
        prompts = [DREAM_PROMPT_POOL[2], DREAM_PROMPT_POOL[3], DREAM_PROMPT_POOL[4]]
    elif signals["work_money"] >= 0.35:
        prompts = [DREAM_PROMPT_POOL[0], DREAM_PROMPT_POOL[4], DREAM_PROMPT_POOL[3]]

    seeds = MICRO_SEEDS[:2]
    if active:
        seeds = MICRO_SEEDS[:3]

    acknowledgment = (
        "솔직히 말하면, 많은 사람이 생활비·돈 때문에 일해요. "
        "그 선택은 현실적이고, 부끄러울 필요가 없어요."
    )
    if signals["work_context"] >= 0.3:
        acknowledgment += " 직장·일의 무게가 크게 느껴지는 것도 자연스러워요."

    return {
        "active": active or universal,
        "universal_framing": universal,
        "signals": signals,
        "headline": "꿈을 심는 시간",
        "subheadline": (
            "돈 때문에 버티는 하루도, 꿈을 키우는 하루가 될 수 있어요. "
            "지금 마음을 돌보며, 작은 미래를 함께 그려봐요."
        ),
        "acknowledgment": acknowledgment,
        "bridge_lines": BRIDGE_LINES[:3],
        "dream_prompts": prompts,
        "micro_seeds": seeds,
        "reflection_question": "지금 하는 일과, 마음속 꿈 — 둘 사이에 다리를 놓는다면 무엇일까요?",
        "chat_directive": (
            "내담자는 생계·돈·일 때문에 버티는 현실을 살고 있을 수 있습니다. "
            "그 이유를 판단하거나 '열정만 있으면 된다'고 말하지 마세요. "
            "대신 '돈 때문에 일하는 건 자연스럽다'고 인정하고, "
            "작은 꿈·미래 상상·다음 한 걸음을 부드럽게 물어보세요. "
            "거창한 성공 스토리보다 오늘부터 가능한 작은 씨앗을 함께 찾아주세요."
        ),
        "value_add": {
            "headline": "생계와 꿈, 둘 다 괜찮아요",
            "subheadline": "지금 버티는 이유를 인정하고, 그 위에 심을 작은 꿈을 찾아요.",
            "points": [
                "돈·일 스트레스를 숫자와 패턴으로 정리",
                "꿈과 연결되는 아주 작은 행동 하나 설계",
                "번아웃·이직 충동 전에 마음 신호 먼저 확인",
            ],
        },
    }


def enrich_case_preview_with_dream(preview: Dict[str, Any], dream: Dict[str, Any]) -> Dict[str, Any]:
    """case_preview에 꿈 심기 블록·미래 비전 보강."""
    out = dict(preview)
    out["dream_seed"] = dream
    if dream.get("active"):
        va = dream.get("value_add") or {}
        vp = dict(out.get("value_proposition") or {})
        vp["dream_headline"] = va.get("headline")
        vp["dream_subheadline"] = va.get("subheadline")
        out["value_proposition"] = vp
        extra = list(va.get("points") or [])
        future = list(out.get("future_vision") or [])
        out["future_vision"] = list(dict.fromkeys(extra + future))[:5]
    return out
