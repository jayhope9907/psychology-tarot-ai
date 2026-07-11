"""마음 돌보기(검사) — 사용자 눈높이 쉬운 말 (임상·검사 용어 최소화)."""
from __future__ import annotations

from typing import Any, Dict, Optional

HUB = {
    "title": "나를 알아가는 시간",
    "subtitle": "검사가 아니라, 지금 마음을 가볍게 들여다보는 공간이에요.",
    "tab_label": "마음 돌보기",
    "short_label": "마음 돌보기",
    "emoji": "💚",
    "disclaimer": (
        "정답은 없어요. 편한 만큼만, 넘어가도 괜찮아요. "
        "이곳은 의료·진단이 아닌 자기탐색·웰니스 도구예요."
    ),
    "progress_label": "나의 마음 돌보기 진행",
}

DREAM_SEED_HUB = {
    "headline": "꿈을 심는 시간",
    "acknowledgment": (
        "많은 사람이 생활비·돈 때문에 일해요. 그건 현실이고, 부끄러울 이유가 아니에요."
    ),
    "subheadline": (
        "지금 버티는 하루도, 꿈을 키우는 하루가 될 수 있어요. "
        "마음을 돌보며 작은 미래를 함께 그려봐요."
    ),
    "cta": "대화에서 꿈 이야기하기",
    "route": "/chat",
}

TRACKS = {
    "screening": {
        "track_id": "screening",
        "label": "짧게 확인하기",
        "user_title": "짧게 확인하기",
        "description": "기분·걱정·잠·스트레스·관계 등, 대화처럼 가볍게 여쭤봐요.",
        "cta": "질문 시작하기",
    },
    "projective": {
        "track_id": "projective",
        "label": "그림·이야기로 표현하기",
        "user_title": "그림·이야기로 표현하기",
        "description": "그림 그리기, 잉크 그림 상상, 이야기 붙이기, 문장 이어쓰기로 마음을 표현해요.",
        "cta": "표현하기 시작",
    },
}

DOMAIN_USER_LABELS: Dict[str, str] = {
    "clinical_mood": "요즘 기분·에너지",
    "clinical_anxiety": "걱정·불안한 마음",
    "clinical_sleep": "잠·수면",
    "clinical_stress": "스트레스·버거움",
    "clinical_trauma": "힘든 기억·마음",
    "wellbeing_self": "나를 바라보는 마음",
    "wellbeing_attachment": "가까움·관계",
    "cbt_cognitive": "자주 드는 생각",
    "psychodynamic": "반복되는 패턴",
    "behavioral": "움직임·즐거움",
    "projective_htp": "집·나무·사람",
    "projective_tarot": "마음에 닿는 그림",
    "humanistic_affect": "지금 마음 무게",
    "projective_sct": "문장 이어쓰기",
    "projective_dap": "사람 그림",
    "projective_kfd": "가족 그림",
    "projective_rorschach": "잉크 그림 상상",
    "projective_tat": "그림 이야기",
}

PROJECTIVE_USER_VOICE: Dict[str, Dict[str, str]] = {
    "htp": {
        "user_title": "집·나무·사람 그리기",
        "intro": "세 가지 그림으로 지금 마음을 표현해 보세요. 그림 실력은 중요하지 않아요.",
    },
    "dap": {
        "user_title": "사람 한 명 그리기",
        "intro": "머릿속에 떠오르는 사람을 자유롭게 그려 주세요.",
    },
    "kfd": {
        "user_title": "가족·가까운 사람 그리기",
        "intro": "함께 있는 모습을 그리며 관계를 떠올려 보세요.",
    },
    "rorschach": {
        "user_title": "잉크 그림 상상하기",
        "intro": "무엇처럼 보이는지 자유롭게 말해 주세요. 정답은 없어요.",
    },
    "tat": {
        "user_title": "그림에 이야기 붙이기",
        "intro": "그림 속 장면에 어떤 일이 일어나는지 상상해 주세요.",
    },
    "sct": {
        "user_title": "문장 이어쓰기",
        "intro": "시작 문장 뒤에 지금 마음을 한두 문장만 이어 써 주세요.",
    },
}

PICTURE_HUB = {
    "title": "그림으로 마음 표현하기",
    "subtitle": "그림·이야기·상상으로 지금 마음을 표현하는 시간이에요.",
}


def friendly_domain_label(domain_id: str, fallback: str = "") -> str:
    return DOMAIN_USER_LABELS.get(domain_id, fallback or domain_id)


def apply_user_voice_to_catalog(catalog: Dict[str, Any]) -> Dict[str, Any]:
    """API 응답에 사용자 친화 레이블을 입힌다."""
    out = dict(catalog)
    out["user_title"] = HUB["title"]
    out["user_subtitle"] = HUB["subtitle"]
    out["user_disclaimer"] = HUB["disclaimer"]
    out["tab_label"] = HUB["tab_label"]
    out["dream_seed_hub"] = DREAM_SEED_HUB

    tracks = []
    for t in out.get("tracks") or []:
        tid = t.get("track_id", "")
        uv = TRACKS.get(tid, {})
        tracks.append({**t, **{k: v for k, v in uv.items() if k not in ("track_id",)}})
    out["tracks"] = tracks

    domains = []
    for d in out.get("domains") or []:
        did = d.get("domain_id", "")
        domains.append({**d, "user_label": friendly_domain_label(did, d.get("label", ""))})
    out["domains"] = domains

    formal = []
    for f in out.get("formal_instruments") or []:
        formal.append(
            {
                **f,
                "user_display_name": f.get("user_title") or f.get("display_name"),
            }
        )
    out["formal_instruments"] = formal

    proj = []
    for p in out.get("projective_instruments") or []:
        iid = p.get("instrument_id", "")
        voice = PROJECTIVE_USER_VOICE.get(iid, {})
        proj.append(
            {
                **p,
                "user_title": voice.get("user_title") or p.get("display_name"),
                "user_intro": voice.get("intro") or p.get("intro"),
            }
        )
    out["projective_instruments"] = proj
    return out
