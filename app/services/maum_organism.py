"""마음쉼터 유기체 — 기능 간 거미줄형 연결·타임라인·다음 행동."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.services.clinical_pipeline import (
    extract_tarot_draw_signals,
    get_user_psych_profile,
    mood_dimension_scores,
    merge_spectrum_scores,
    recommendations_from_spectra,
    build_pipeline_status,
)
from app.services.daily_routine import build_dashboard, today_checkin
from app.services.persistence import load_latest_session_for_user
from app.services.psych_timeline import list_events, load_profile, record_event, save_profile

FEATURE_NODES: Dict[str, Dict[str, str]] = {
    "checkin": {"emoji": "💚", "label": "오늘 마음", "tab": "checkin", "route": "/home"},
    "tarot": {"emoji": "✦", "label": "타로", "tab": "tarot", "route": "/tarot"},
    "chat": {"emoji": "💬", "label": "AI 대화", "tab": "chat", "route": "/chat"},
    "picto": {"emoji": "🖼️", "label": "그림 마음", "tab": "picto", "route": "/picto"},
    "clinical": {"emoji": "💚", "label": "마음 돌보기", "tab": "clinical", "route": "/clinical"},
}

# 기능 간 기본 연결 (거미줄 골격)
DEFAULT_EDGES: List[Tuple[str, str, str]] = [
    ("checkin", "chat", "기분 → 대화"),
    ("checkin", "tarot", "기분 → 타로"),
    ("tarot", "chat", "타로 → 대화"),
    ("picto", "checkin", "그림 → 기분"),
    ("picto", "chat", "그림 → 대화"),
    ("checkin", "clinical", "기분 → 검사"),
    ("chat", "clinical", "대화 → 검사"),
    ("clinical", "chat", "검사 → 대화"),
    ("tarot", "picto", "타로 → 그림"),
    ("clinical", "picto", "표현 → 그림"),
]

EVENT_FEATURE_MAP: Dict[str, str] = {
    "mood_checkin": "checkin",
    "picto_checkin": "picto",
    "picto_chat": "picto",
    "picto_card": "picto",
    "picto_caregiver_alert": "picto",
    "tarot_draw": "tarot",
    "tarot_exploration": "tarot",
    "counseling_session": "chat",
    "assessment_answer": "clinical",
    "projective_answer": "clinical",
}


def _utc_today() -> str:
    return date.today().isoformat()


def _event_feature(event_type: str, payload: Dict[str, Any]) -> str:
    if event_type in EVENT_FEATURE_MAP:
        return EVENT_FEATURE_MAP[event_type]
    if event_type == "mood_checkin" and "[그림" in str(payload.get("note") or ""):
        return "picto"
    return "chat"


def emit_activity(
    user_id: str,
    event_type: str,
    payload: Dict[str, Any],
    *,
    source_id: str = "",
    event_at: Optional[str] = None,
) -> int:
    """모든 기능의 공통 활동 기록."""
    enriched = {**payload, "feature": _event_feature(event_type, payload)}
    return record_event(user_id, event_type, enriched, event_at=event_at, source_id=source_id)


def sync_after_checkin(
    user_id: str,
    checkin: Dict[str, Any],
    *,
    source: str = "checkin",
    picto_id: Optional[str] = None,
) -> Dict[str, Any]:
    """체크인 즉시 타임라인·프로필 반영."""
    mood_sig = mood_dimension_scores([checkin])
    event_type = "picto_checkin" if source == "picto" else "mood_checkin"
    checkin_date = checkin.get("checkin_date") or _utc_today()
    emit_activity(
        user_id,
        event_type,
        {
            "mood_score": checkin.get("mood_score"),
            "dimensions": checkin.get("dimensions"),
            "note": checkin.get("note"),
            "picto_id": picto_id,
            "signals": mood_sig,
        },
        source_id=f"{source}:{checkin_date}",
        event_at=checkin_date,
    )
    profile = load_profile(user_id) or {}
    merged = merge_spectrum_scores(profile.get("domain_scores") or {}, mood_sig)
    recs = recommendations_from_spectra(merged)
    stages = profile.get("pipeline_stages") or {}
    profile.update(
        {
            "user_id": user_id,
            "domain_scores": merged,
            "recommendations": recs,
            "last_checkin_date": checkin_date,
            "last_mood_score": checkin.get("mood_score"),
            "pipeline_stages": stages,
        }
    )
    profile["pipeline_status"] = build_pipeline_status(profile)
    save_profile(user_id, profile)
    return profile


def sync_after_tarot_draw(user_id: str, draw: Dict[str, Any], *, draw_id: Optional[int] = None) -> Dict[str, Any]:
    """타로 뽑기 직후 — 브릿지 없이도 프로필·타임라인 연동."""
    signals = extract_tarot_draw_signals(draw)
    cards = draw.get("cards") or []
    emit_activity(
        user_id,
        "tarot_draw",
        {
            "draw_id": draw_id,
            "spread": draw.get("spread"),
            "signals": signals,
            "card_names": [c.get("name_ko") for c in cards[:3]],
            "themes": [c.get("psychology_theme") for c in cards if c.get("psychology_theme")],
        },
        source_id=f"draw:{draw_id or draw.get('spread')}",
    )
    profile = load_profile(user_id) or {}
    merged = merge_spectrum_scores(profile.get("domain_scores") or {}, signals)
    stages = profile.get("pipeline_stages") or {}
    stages["tarot_exploration"] = True
    profile.update(
        {
            "user_id": user_id,
            "domain_scores": merged,
            "last_tarot_signals": signals,
            "recommendations": recommendations_from_spectra(merged),
            "pipeline_stages": stages,
        }
    )
    profile["pipeline_status"] = build_pipeline_status(profile)
    save_profile(user_id, profile)
    return profile


def sync_after_picto_chat(user_id: str, session_id: str, picto_ids: List[str]) -> None:
    emit_activity(
        user_id,
        "picto_chat",
        {"session_id": session_id, "picto_ids": picto_ids},
        source_id=f"picto_chat:{session_id}:{len(picto_ids)}",
    )


def _node_pulse(events: List[Dict[str, Any]], today: str) -> Dict[str, float]:
    pulse = {key: 0.15 for key in FEATURE_NODES}
    for ev in events:
        feature = _event_feature(ev.get("event_type", ""), ev.get("payload") or {})
        if feature not in pulse:
            continue
        pulse[feature] = min(1.0, pulse[feature] + 0.35)
        if (ev.get("event_at") or "").startswith(today):
            pulse[feature] = min(1.0, pulse[feature] + 0.25)
    return pulse


def _build_edges(events: List[Dict[str, Any]], pulse: Dict[str, float]) -> List[Dict[str, Any]]:
    active = {k for k, v in pulse.items() if v > 0.2}
    edges: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str]] = set()

    def add_edge(a: str, b: str, label: str, strength: float) -> None:
        key = tuple(sorted((a, b)))
        if key in seen:
            return
        seen.add(key)
        edges.append({"from": a, "to": b, "label": label, "strength": round(strength, 2)})

    for a, b, label in DEFAULT_EDGES:
        base = 0.25
        if a in active and b in active:
            base = 0.85
        elif a in active or b in active:
            base = 0.45
        add_edge(a, b, label, base)

    # 최근 연쇄: 같은 날 발생한 기능 쌍 강화
    by_day: Dict[str, set[str]] = {}
    for ev in events[:15]:
        day = (ev.get("event_at") or "")[:10]
        feat = _event_feature(ev.get("event_type", ""), ev.get("payload") or {})
        by_day.setdefault(day, set()).add(feat)
    for feats in by_day.values():
        flist = sorted(feats)
        for i, a in enumerate(flist):
            for b in flist[i + 1 :]:
                add_edge(a, b, "오늘 함께", 0.95)

    return edges


def _build_threads(events: List[Dict[str, Any]], limit: int = 12) -> List[Dict[str, Any]]:
    threads: List[Dict[str, Any]] = []
    for ev in events[:limit]:
        et = ev.get("event_type", "")
        payload = ev.get("payload") or {}
        feature = _event_feature(et, payload)
        node = FEATURE_NODES.get(feature, FEATURE_NODES["chat"])
        threads.append(
            {
                "event_type": et,
                "feature": feature,
                "emoji": node["emoji"],
                "label": node["label"],
                "at": ev.get("event_at"),
                "summary": _thread_summary(et, payload),
            }
        )
    return threads


def _thread_summary(event_type: str, payload: Dict[str, Any]) -> str:
    if event_type in ("mood_checkin", "picto_checkin"):
        return f"기분 {payload.get('mood_score', '')}/5"
    if event_type == "tarot_draw":
        names = payload.get("card_names") or []
        return " · ".join(names) if names else "카드 뽑기"
    if event_type == "tarot_exploration":
        return str(payload.get("primary_card") or "타로 탐색")
    if event_type == "counseling_session":
        return f"대화 {payload.get('turn_count', '')}턴"
    if event_type == "picto_chat":
        return "그림 대화"
    if event_type == "picto_caregiver_alert":
        return "보호자 알림"
    if event_type == "projective_answer":
        return str(payload.get("instrument") or "그림·이야기 표현")
    if event_type == "assessment_answer":
        return str(payload.get("instrument") or "검사")
    return event_type


def _build_next_actions(
    user_id: str,
    dashboard: Dict[str, Any],
    profile: Dict[str, Any],
    session: Any,
) -> List[Dict[str, str]]:
    actions: List[Dict[str, str]] = []
    today = dashboard.get("today_checkin")
    tarot = dashboard.get("recent_tarot") or []
    has_session = bool(session and session.turn_count)

    if not today:
        actions.append(
            {"tab": "checkin", "emoji": "💚", "label": "오늘 마음 남기기", "reason": "모든 기능의 시작점"}
        )
    if tarot and not has_session:
        actions.append(
            {"tab": "chat", "emoji": "💬", "label": "타로 이야기 이어가기", "reason": "방금 카드와 연결"}
        )
    elif today and not tarot:
        actions.append(
            {"tab": "tarot", "emoji": "✦", "label": "기분에 맞는 카드", "reason": "오늘 마음과 타로 연결"}
        )
    if session and session.pending_homework:
        actions.append(
            {"tab": "chat", "emoji": "📝", "label": "숙제 이어하기", "reason": "대화에서 이어짐"}
        )
    recs = (profile or {}).get("recommendations") or {}
    if recs.get("instruments") and not (session and session.formal_answers):
        actions.append(
            {"tab": "clinical", "emoji": "💚", "label": "마음 돌보기", "reason": "프로필·대화 기반"}
        )
    proj = ((session.quant_features or {}).get("projective_battery") or {}).get("answers") if session else None
    if session and session.formal_answers and not proj:
        actions.append(
            {"tab": "clinical", "emoji": "🖼️", "label": "그림으로 표현하기", "reason": "짧게 확인 후 이어하기"}
        )
    if len(actions) < 3:
        actions.append(
            {"tab": "picto", "emoji": "🖼️", "label": "그림으로 표현", "reason": "기분·대화와 연결"}
        )
    return actions[:4]


def build_organism_state(user_id: str) -> Dict[str, Any]:
    """거미줄형 유기체 상태 — 모든 기능의 연결·맥박·다음 행동."""
    dashboard = build_dashboard(user_id)
    profile = get_user_psych_profile(user_id, auto_backfill=True)
    session = load_latest_session_for_user(user_id)
    events = list_events(user_id, 30)
    today = _utc_today()
    pulse = _node_pulse(events, today)

    nodes = [
        {
            "id": fid,
            **meta,
            "pulse": round(pulse.get(fid, 0.15), 2),
            "active_today": pulse.get(fid, 0) > 0.5,
        }
        for fid, meta in FEATURE_NODES.items()
    ]

    unified_session = None
    if session:
        unified_session = session.session_id
    elif dashboard.get("session_id"):
        unified_session = dashboard["session_id"]

    return {
        "user_id": user_id,
        "mode": "organism",
        "description": "기분·타로·대화·그림·마음 돌보기가 하나의 마음 이야기로 연결됩니다.",
        "unified_session_id": unified_session,
        "nodes": nodes,
        "edges": _build_edges(events, pulse),
        "threads": _build_threads(events),
        "next_actions": _build_next_actions(user_id, dashboard, profile, session),
        "dashboard": {
            "greeting": dashboard.get("greeting"),
            "today_checkin": bool(dashboard.get("today_checkin")),
            "counseling_phase": dashboard.get("counseling_phase"),
            "homework_pending": dashboard.get("homework_pending"),
            "recent_tarot_count": len(dashboard.get("recent_tarot") or []),
        },
        "profile": {
            "pipeline_status": profile.get("pipeline_status"),
            "top_spectra": (profile.get("recommendations") or {}).get("top_spectra", [])[:3],
            "disclaimer": profile.get("disclaimer"),
        },
        "storage_keys": {
            "user_id": "psychology_ai_user_id",
            "session_id": "psychology_ai_session_id",
        },
    }
