"""표현·역할·연극치료 가이드 세션 — 말·글이 어려운 내담자용."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.models.clinical import ClinicalSchool

STORE_KEY = "expressive_therapy"

DISCLAIMER_KO = (
    "표현·역할·연극 기법은 자기성찰·교육용 가이드입니다. "
    "정식 사이코드라마·연극치료를 대체하지 않으며, 힘들면 언제든 멈출 수 있습니다."
)

SCHOLARS = [
    {
        "id": "moreno",
        "name": "Jacob L. Moreno",
        "name_ko": "제이콥 모레노",
        "school": ClinicalSchool.PSYCHODRAMA.value,
        "focus": "사이코드라마 · 역할극 · 자발성",
        "techniques": ["역할극", "역할 바꾸기", "더블링", "미러링", "장면 구성"],
    },
    {
        "id": "perls",
        "name": "Fritz Perls",
        "name_ko": "프리츠 펄스",
        "school": ClinicalSchool.GESTALT.value,
        "focus": "게슈탈트 · 빈 의자 · 지금-여기",
        "techniques": ["빈 의자", "역할 바꾸기", "신체 알아차림"],
    },
    {
        "id": "emunah",
        "name": "Renee Emunah",
        "name_ko": "르네 에무나",
        "school": ClinicalSchool.DRAMA_THERAPY.value,
        "focus": "연극치료 · 과정 중심 표현",
        "techniques": ["연극적 거리두기", "즉흥", "감정 외현화"],
    },
    {
        "id": "jones",
        "name": "Phil Jones",
        "name_ko": "필 존스",
        "school": ClinicalSchool.DRAMA_THERAPY.value,
        "focus": "드라마 테라피 · 상징·몸",
        "techniques": ["상징 표현", "스토리 만들기", "안전한 종결"],
    },
]

ROLE_CARDS = [
    {"id": "self_now", "emoji": "🧍", "label": "지금의 나", "prompt": "지금 이 순간 나의 마음·몸"},
    {"id": "inner_child", "emoji": "🧒", "label": "어린 나", "prompt": "예전의 나, 보호가 필요했던 나"},
    {"id": "critic", "emoji": "🪞", "label": "비판하는 목소리", "prompt": "나를 다그치는 속목소리"},
    {"id": "supporter", "emoji": "🤝", "label": "응원하는 나", "prompt": "나를 지켜주는 따뜻한 목소리"},
    {"id": "other_person", "emoji": "👤", "label": "상대방", "prompt": "말하고 싶은 사람·관계"},
    {"id": "body", "emoji": "🫀", "label": "몸의 감각", "prompt": "말로 하기 전에 몸이 말하는 것"},
    {"id": "future_self", "emoji": "🌅", "label": "미래의 나", "prompt": "조금 더 편한 미래의 나"},
    {"id": "symbol", "emoji": "🎭", "label": "상징·소품", "prompt": "감정 대신 물건·상징으로 표현"},
]

PIC_RESPONSES = [
    {"id": "ok", "emoji": "🙂", "label": "괜찮아요"},
    {"id": "hard", "emoji": "😣", "label": "힘들어요"},
    {"id": "confused", "emoji": "😕", "label": "헷갈려요"},
    {"id": "warm", "emoji": "💛", "label": "따뜻해요"},
    {"id": "scared", "emoji": "😨", "label": "무서워요"},
    {"id": "stop", "emoji": "🛑", "label": "그만할래요"},
    {"id": "more", "emoji": "➕", "label": "조금 더"},
    {"id": "quiet", "emoji": "🤫", "label": "말없이"},
]

MODES: Dict[str, Dict[str, Any]] = {
    "empty_chair": {
        "mode_id": "empty_chair",
        "title": "빈 의자 기법",
        "scholar": "Fritz Perls (게슈탈트)",
        "school": ClinicalSchool.GESTALT.value,
        "user_blurb": "말하기 어려울 때, 빈 자리에 마음을 앉혀 보는 연습",
        "duration_hint": "약 8–12분",
        "steps": [
            {
                "step_id": "safety",
                "title": "안전 확인",
                "prompt": "지금 몸과 마음이 이 연습을 해도 괜찮은가요? 힘들면 언제든 멈춰도 됩니다.",
                "input": "choice",
                "choices": ["시작할래요", "오늘은 쉬고 싶어요"],
            },
            {
                "step_id": "place",
                "title": "빈 자리 정하기",
                "prompt": "앞에 빈 자리(또는 방석·인형)를 하나 상상해 보세요. 누구/무엇을 앉히고 싶나요?",
                "input": "role_or_text",
            },
            {
                "step_id": "body",
                "title": "몸 알아차림",
                "prompt": "그 자리를 바라볼 때 몸에서 느껴지는 감각을 골라 보세요. 말로 안 해도 됩니다.",
                "input": "picto",
            },
            {
                "step_id": "speak_to",
                "title": "말하기 (또는 마음말로)",
                "prompt": "그 자리에 있는 존재에게, 하고 싶었던 한 문장(또는 이모지)을 남겨 보세요.",
                "input": "text_or_picto",
            },
            {
                "step_id": "switch",
                "title": "자리 바꾸기",
                "prompt": "이제 그 자리에 앉아 본다고 상상해 보세요. 그 존재라면 뭐라고 답할까요?",
                "input": "text_or_picto",
            },
            {
                "step_id": "return",
                "title": "나에게로 돌아오기",
                "prompt": "다시 ‘지금의 나’로 돌아와, 방금 경험에서 남은 감각·감정을 골라 주세요.",
                "input": "picto",
            },
            {
                "step_id": "close",
                "title": "마무리",
                "prompt": "연습이 끝났어요. 오늘 자신에게 해주고 싶은 짧은 말이 있나요? (없어도 괜찮아요)",
                "input": "text_or_picto",
            },
        ],
    },
    "role_play": {
        "mode_id": "role_play",
        "title": "역할극 · 롤플레잉",
        "scholar": "J.L. Moreno (사이코드라마)",
        "school": ClinicalSchool.PSYCHODRAMA.value,
        "user_blurb": "역할을 빌려 장면으로 마음을 표현하는 연습",
        "duration_hint": "약 10분",
        "steps": [
            {
                "step_id": "warmup",
                "title": "워밍업",
                "prompt": "지금 기분을 카드로 골라 주세요. 말이 필요 없어요.",
                "input": "picto",
            },
            {
                "step_id": "pick_role",
                "title": "역할 고르기",
                "prompt": "오늘은 어떤 역할로 장면을 만들어 볼까요?",
                "input": "role",
            },
            {
                "step_id": "scene",
                "title": "장면 한 컷",
                "prompt": "그 역할이 있는 짧은 장면을 떠올려 보세요. 장소·상대·한 순간이면 충분해요.",
                "input": "text_or_picto",
            },
            {
                "step_id": "act",
                "title": "한 마디 / 한 동작",
                "prompt": "그 역할이 되어, 하고 싶은 말이나 몸짓(글로 적어도 OK)을 남겨 주세요.",
                "input": "text_or_picto",
            },
            {
                "step_id": "double",
                "title": "더블링 (옆에서 돕기)",
                "prompt": "친구가 옆에서 ‘속마음은 이렇지 않을까요?’라고 말해준다면?",
                "input": "text_or_picto",
            },
            {
                "step_id": "derole",
                "title": "탈역할",
                "prompt": "역할을 내려놓고 ‘지금의 나’로 돌아옵니다. 이름·오늘 날짜를 속으로 확인해 보세요. 어떤 기분인가요?",
                "input": "picto",
            },
            {
                "step_id": "share",
                "title": "나눔",
                "prompt": "이 장면에서 가장 중요했던 감정이나 발견을 한 줄로(또는 카드로) 남겨 주세요.",
                "input": "text_or_picto",
            },
        ],
    },
    "drama_symbol": {
        "mode_id": "drama_symbol",
        "title": "연극·상징 표현",
        "scholar": "Renee Emunah / Phil Jones (연극치료)",
        "school": ClinicalSchool.DRAMA_THERAPY.value,
        "user_blurb": "말 대신 상징·스토리로 거리를 두고 표현하기",
        "duration_hint": "약 8분",
        "steps": [
            {
                "step_id": "distance",
                "title": "거리두기",
                "prompt": "이야기를 ‘내 일’이 아니라 ‘어떤 인물의 이야기’처럼 바라봐도 괜찮아요. 준비됐나요?",
                "input": "choice",
                "choices": ["네, 해볼게요", "조금 천천히"],
            },
            {
                "step_id": "symbol",
                "title": "상징 고르기",
                "prompt": "지금 마음을 대신할 상징·소품을 골라 보세요.",
                "input": "role",
            },
            {
                "step_id": "story",
                "title": "짧은 스토리",
                "prompt": "그 상징이 주인공인 아주 짧은 이야기를 만들어 보세요. (한두 문장 또는 카드)",
                "input": "text_or_picto",
            },
            {
                "step_id": "feeling",
                "title": "감정 외현화",
                "prompt": "이야기 속 인물이 느끼는 감정을 카드로 고르면 됩니다.",
                "input": "picto",
            },
            {
                "step_id": "close_ritual",
                "title": "종결 의식",
                "prompt": "상상의 막을 내리고, 심호흡 한 번. 오늘의 나에게 남겨줄 카드는?",
                "input": "picto",
            },
        ],
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def expressive_catalog() -> Dict[str, Any]:
    return {
        "title": "표현·역할·연극 연습",
        "subtitle": "말이나 글이 어려울 때, 역할·빈 의자·상징으로 마음을 표현해 보세요",
        "disclaimer": DISCLAIMER_KO,
        "scholars": SCHOLARS,
        "role_cards": ROLE_CARDS,
        "picto_responses": PIC_RESPONSES,
        "modes": [
            {
                "mode_id": m["mode_id"],
                "title": m["title"],
                "scholar": m["scholar"],
                "school": m["school"],
                "user_blurb": m["user_blurb"],
                "duration_hint": m["duration_hint"],
                "step_count": len(m["steps"]),
            }
            for m in MODES.values()
        ],
        "safety": {
            "stop_anytime": True,
            "crisis": "위급하면 1393 · 119 · 129",
        },
    }


def _store(session) -> Dict[str, Any]:
    qf = session.quant_features.setdefault(STORE_KEY, {})
    qf.setdefault("sessions", {})
    return qf


def start_expressive_session(session, mode_id: str) -> Dict[str, Any]:
    mode = MODES.get(mode_id)
    if not mode:
        return {"ok": False, "error": "unknown_mode"}
    sid = f"ex-{secrets.token_hex(4)}"
    store = _store(session)
    state = {
        "session_id": sid,
        "mode_id": mode_id,
        "school": mode["school"],
        "step_index": 0,
        "responses": [],
        "started_at": _utc_now(),
        "completed": False,
        "stopped": False,
    }
    store["sessions"][sid] = state
    store["active_session_id"] = sid
    return {
        "ok": True,
        "session": _public_session(state, mode),
        "step": mode["steps"][0],
        "disclaimer": DISCLAIMER_KO,
    }


def _public_session(state: Dict[str, Any], mode: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "session_id": state["session_id"],
        "mode_id": state["mode_id"],
        "title": mode["title"],
        "scholar": mode["scholar"],
        "school": state["school"],
        "step_index": state["step_index"],
        "step_total": len(mode["steps"]),
        "completed": state.get("completed"),
        "stopped": state.get("stopped"),
    }


def advance_expressive_step(
    session,
    *,
    expressive_session_id: str,
    response: Optional[Dict[str, Any]] = None,
    stop: bool = False,
) -> Dict[str, Any]:
    store = _store(session)
    state = (store.get("sessions") or {}).get(expressive_session_id)
    if not state:
        return {"ok": False, "error": "session_not_found"}
    mode = MODES.get(state["mode_id"])
    if not mode:
        return {"ok": False, "error": "unknown_mode"}

    if stop:
        state["stopped"] = True
        state["completed"] = True
        state["ended_at"] = _utc_now()
        return {
            "ok": True,
            "stopped": True,
            "session": _public_session(state, mode),
            "summary": build_session_summary(state, mode),
            "message_ko": "안전하게 멈췄어요. 잘하셨어요.",
        }

    steps = mode["steps"]
    idx = int(state.get("step_index") or 0)
    if idx >= len(steps):
        state["completed"] = True
        return {"ok": True, "completed": True, "session": _public_session(state, mode), "summary": build_session_summary(state, mode)}

    current = steps[idx]
    resp = response or {}
    # safety: picto stop
    if resp.get("picto_id") == "stop" or resp.get("choice") == "오늘은 쉬고 싶어요":
        return advance_expressive_step(session, expressive_session_id=expressive_session_id, stop=True)

    state["responses"].append(
        {
            "step_id": current["step_id"],
            "response": resp,
            "at": _utc_now(),
        }
    )
    idx += 1
    state["step_index"] = idx

    if idx >= len(steps):
        state["completed"] = True
        state["ended_at"] = _utc_now()
        summary = build_session_summary(state, mode)
        return {
            "ok": True,
            "completed": True,
            "session": _public_session(state, mode),
            "summary": summary,
            "message_ko": "연습을 마쳤어요. 말은 적어도, 표현은 충분히 의미 있어요.",
        }

    return {
        "ok": True,
        "session": _public_session(state, mode),
        "step": steps[idx],
        "progress": {"index": idx + 1, "total": len(steps)},
    }


def build_session_summary(state: Dict[str, Any], mode: Dict[str, Any]) -> Dict[str, Any]:
    responses = state.get("responses") or []
    return {
        "mode_id": mode["mode_id"],
        "title": mode["title"],
        "scholar": mode["scholar"],
        "school": mode["school"],
        "response_count": len(responses),
        "completed": bool(state.get("completed")),
        "stopped": bool(state.get("stopped")),
        "highlights": [
            {
                "step_id": r.get("step_id"),
                "response": r.get("response"),
            }
            for r in responses[-4:]
        ],
        "reflection_ko": (
            "역할·빈 의자·상징 표현은 ‘잘 말하는 것’이 목표가 아닙니다. "
            "오늘 남긴 감각과 장면을 부드럽게 기억해 두세요."
        ),
        "disclaimer_ko": DISCLAIMER_KO,
    }


def get_active_expressive(session) -> Optional[Dict[str, Any]]:
    store = _store(session)
    sid = store.get("active_session_id")
    if not sid:
        return None
    state = (store.get("sessions") or {}).get(sid)
    if not state or state.get("completed"):
        return None
    mode = MODES.get(state["mode_id"])
    if not mode:
        return None
    idx = int(state.get("step_index") or 0)
    step = mode["steps"][idx] if idx < len(mode["steps"]) else None
    return {"session": _public_session(state, mode), "step": step}
