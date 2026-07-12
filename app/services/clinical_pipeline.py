"""Tarot → counseling → DSM-5 screening → assessment/technique tracking pipeline."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.assessments import ALL_INSTRUMENTS
from app.services.chat_session import ChatSessionState
from app.services.daily_routine import recent_checkins
from app.services.dsm5_framework import (
    DSM5_SPECTRA,
    merge_spectrum_scores,
    recommendations_from_spectra,
    score_text_against_spectra,
)
from app.services.persistence import list_tarot_draws, list_user_sessions, load_session
from app.services.psych_timeline import list_events, load_profile, record_event, save_profile

# 타로 심리 테마 → DSM 스크리닝 영역
TAROT_THEME_TO_SPECTRUM: Dict[str, str] = {
    "불안": "anxiety_disorders",
    "걱정": "anxiety_disorders",
    "우울": "depressive_disorders",
    "슬픔": "depressive_disorders",
    "무기력": "depressive_disorders",
    "외상": "trauma_stressor",
    "상실": "depressive_disorders",
    "관계": "personality_interpersonal",
    "애착": "personality_interpersonal",
    "수면": "sleep_wake",
    "피로": "sleep_wake",
    "강박": "ocd_related",
    "통제": "ocd_related",
    "중독": "substance_behavioral",
    "신체": "somatic_distress",
    "변화": "bipolar_spectrum",
    "에너지": "bipolar_spectrum",
    "집중": "neurodevelopmental",
    "해리": "dissociative_stress",
    "섭식": "eating_body",
}


def _messages_blob(messages: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for msg in messages or []:
        role = msg.get("role")
        if role in ("user", "assistant"):
            parts.append(str(msg.get("content") or ""))
    return "\n".join(parts)


def extract_tarot_signals(handoff: Optional[Dict[str, Any]]) -> Dict[str, float]:
    if not handoff:
        return {}
    scores: Dict[str, float] = {}
    blob_parts: List[str] = []

    for theme in handoff.get("psychology_themes") or []:
        blob_parts.append(str(theme))
        for key, spectrum in TAROT_THEME_TO_SPECTRUM.items():
            if key in str(theme):
                scores[spectrum] = min(1.0, scores.get(spectrum, 0.0) + 0.35)

    for card in handoff.get("cards") or []:
        for field in ("psychology_theme", "meaning", "archetype", "name_ko"):
            blob_parts.append(str(card.get(field) or ""))

    blob_parts.append(handoff.get("user_story") or "")
    blob_parts.append(handoff.get("reading_summary") or "")
    blob_parts.append(handoff.get("ai_analysis") or "")

    text_scores = score_text_against_spectra(" ".join(blob_parts))
    return merge_spectrum_scores(scores, text_scores)


def extract_tarot_draw_signals(draw: Dict[str, Any]) -> Dict[str, float]:
    blob_parts: List[str] = []
    for card in draw.get("cards") or []:
        for field in ("psychology_theme", "meaning_ko", "archetype", "name_ko"):
            blob_parts.append(str(card.get(field) or ""))
    return score_text_against_spectra(" ".join(blob_parts))


def mood_dimension_scores(checkins: List[Dict[str, Any]]) -> Dict[str, float]:
    if not checkins:
        return {}
    latest = checkins[0]
    dims = latest.get("dimensions") or {}
    scores: Dict[str, float] = {}

    valence = int(dims.get("valence", 3))
    if valence <= 2:
        scores["depressive_disorders"] = 0.45
    energy = int(dims.get("energy", 3))
    if energy <= 2:
        scores["depressive_disorders"] = min(1.0, scores.get("depressive_disorders", 0.0) + 0.25)
    if energy >= 5 and valence >= 4:
        scores["bipolar_spectrum"] = 0.35

    anxiety = int(dims.get("anxiety", 3))
    if anxiety >= 4:
        scores["anxiety_disorders"] = min(1.0, 0.35 + (anxiety - 3) * 0.15)

    sleep = int(dims.get("sleep", 3))
    if sleep <= 2:
        scores["sleep_wake"] = min(1.0, 0.4 + (3 - sleep) * 0.12)

    social = int(dims.get("social", 3))
    if social <= 2:
        scores["personality_interpersonal"] = 0.3

    note = latest.get("note") or ""
    if note:
        scores = merge_spectrum_scores(scores, score_text_against_spectra(note))
    return scores


def formal_answer_scores(formal_answers: Dict[str, Any]) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for instrument_id, answers in (formal_answers or {}).items():
        if instrument_id not in ALL_INSTRUMENTS or not answers:
            continue
        try:
            scored = ALL_INSTRUMENTS[instrument_id].score_partial(answers)
        except Exception:
            continue
        severity = str(scored.get("severity_hint") or scored.get("severity") or "").lower()
        risk = {
            "minimal": 0.05,
            "normal": 0.05,
            "mild": 0.35,
            "moderate": 0.55,
            "severe": 0.75,
            "screen_positive": 0.7,
        }.get(severity, 0.2 if severity else 0.0)
        if risk <= 0:
            continue
        from app.services.dsm5_framework import instrument_to_spectrum

        spectrum = instrument_to_spectrum(instrument_id)
        if spectrum:
            scores[spectrum] = max(scores.get(spectrum, 0.0), risk)
    return scores


def aggregate_domain_scores(
    *,
    tarot_signals: Optional[Dict[str, float]] = None,
    mood_signals: Optional[Dict[str, float]] = None,
    text: str = "",
    formal_answers: Optional[Dict[str, Any]] = None,
) -> Dict[str, float]:
    return merge_spectrum_scores(
        tarot_signals or {},
        mood_signals or {},
        score_text_against_spectra(text),
        formal_answer_scores(formal_answers or {}),
    )


def build_pipeline_status(profile: Dict[str, Any]) -> Dict[str, Any]:
    stages = profile.get("pipeline_stages") or {}
    return {
        "tarot_exploration": bool(stages.get("tarot_exploration")),
        "counseling": bool(stages.get("counseling")),
        "recommendations": bool(stages.get("recommendations")),
        "tracking": bool(profile.get("tracked_instruments") or profile.get("tracked_techniques")),
        "backfilled": bool(profile.get("backfill_at")),
    }


def sync_after_tarot(
    user_id: str,
    session_id: Optional[str],
    handoff: Dict[str, Any],
    *,
    draw_id: Optional[int] = None,
    event_at: Optional[str] = None,
) -> Dict[str, Any]:
    signals = extract_tarot_signals(handoff)
    record_event(
        user_id,
        "tarot_exploration",
        {
            "session_id": session_id,
            "draw_id": draw_id,
            "signals": signals,
            "themes": handoff.get("psychology_themes") or [],
            "primary_card": handoff.get("primary_card"),
        },
        event_at=event_at,
        source_id=f"tarot:{session_id or draw_id or 'anon'}",
    )
    profile = load_profile(user_id) or {}
    stages = profile.get("pipeline_stages") or {}
    stages["tarot_exploration"] = True
    merged = merge_spectrum_scores(profile.get("domain_scores") or {}, signals)
    recs = recommendations_from_spectra(merged)
    profile.update(
        {
            "user_id": user_id,
            "pipeline_stages": stages,
            "domain_scores": merged,
            "last_tarot_signals": signals,
            "recommendations": recs,
            "pipeline_status": None,
        }
    )
    profile["pipeline_status"] = build_pipeline_status(profile)
    save_profile(user_id, profile)
    return profile


def sync_after_counseling(
    user_id: str,
    session: ChatSessionState,
    *,
    event_at: Optional[str] = None,
) -> Dict[str, Any]:
    text = _messages_blob(session.messages)
    tarot_signals = extract_tarot_signals(session.tarot_handoff)
    checkins = recent_checkins(user_id, 7)
    mood_signals = mood_dimension_scores(checkins)
    domain_scores = aggregate_domain_scores(
        tarot_signals=tarot_signals,
        mood_signals=mood_signals,
        text=text,
        formal_answers=session.formal_answers,
    )
    recs = recommendations_from_spectra(domain_scores)

    tracked_inst = set((load_profile(user_id) or {}).get("tracked_instruments") or [])
    tracked_tech = set((load_profile(user_id) or {}).get("tracked_techniques") or [])
    for item in recs.get("instruments") or []:
        tracked_inst.add(item["instrument_id"])
    for item in recs.get("techniques") or []:
        tracked_tech.add(item["technique"])

    record_event(
        user_id,
        "counseling_session",
        {
            "session_id": session.session_id,
            "turn_count": session.turn_count,
            "counseling_phase": session.counseling_phase,
            "domain_scores": domain_scores,
            "recommendations": recs,
            "assessments_completed": session.assessments_completed,
            "has_tarot": bool(session.tarot_handoff),
        },
        event_at=event_at,
        source_id=f"session:{session.session_id}",
    )

    profile = load_profile(user_id) or {}
    stages = profile.get("pipeline_stages") or {}
    stages["counseling"] = True
    stages["recommendations"] = True

    profile.update(
        {
            "user_id": user_id,
            "pipeline_stages": stages,
            "domain_scores": domain_scores,
            "recommendations": recs,
            "tracked_instruments": sorted(tracked_inst),
            "tracked_techniques": sorted(tracked_tech),
            "last_session_id": session.session_id,
            "clinical_insight": session.clinical_insight,
            "counseling_phase": session.counseling_phase,
        }
    )
    profile["pipeline_status"] = build_pipeline_status(profile)
    save_profile(user_id, profile)

    try:
        from app.services.user_agent_algorithm import sync_user_agent_from_session

        agent_bundle = sync_user_agent_from_session(user_id, session)
        profile = load_profile(user_id) or profile
        profile["agent_fingerprint"] = agent_bundle.get("agent_fingerprint")
        profile["pattern_hits"] = agent_bundle.get("patterns")
    except Exception:
        pass

    return profile


def backfill_user_profile(user_id: str, *, session_limit: int = 30, draw_limit: int = 50) -> Dict[str, Any]:
    """Rebuild psych profile from historical tarot, mood, and session data."""
    events_written = 0
    domain_scores: Dict[str, float] = {}
    stages = {
        "tarot_exploration": False,
        "counseling": False,
        "recommendations": False,
    }
    tracked_inst: set[str] = set()
    tracked_tech: set[str] = set()
    timeline: List[Dict[str, Any]] = []

    draws = list_tarot_draws(user_id, draw_limit)
    for draw in reversed(draws):
        signals = extract_tarot_draw_signals({"cards": draw.get("cards") or []})
        domain_scores = merge_spectrum_scores(domain_scores, signals)
        if signals:
            stages["tarot_exploration"] = True
        record_event(
            user_id,
            "tarot_exploration",
            {
                "draw_id": draw.get("id"),
                "signals": signals,
                "spread": draw.get("spread"),
                "backfill": True,
            },
            event_at=draw.get("created_at"),
            source_id=f"draw:{draw.get('id')}",
        )
        events_written += 1
        timeline.append({"type": "tarot", "at": draw.get("created_at"), "signals": signals})

    checkins = recent_checkins(user_id, 90)
    for checkin in reversed(checkins):
        mood_sig = mood_dimension_scores([checkin])
        domain_scores = merge_spectrum_scores(domain_scores, mood_sig)
        record_event(
            user_id,
            "mood_checkin",
            {"mood_score": checkin.get("mood_score"), "signals": mood_sig, "backfill": True},
            event_at=checkin.get("checkin_date"),
            source_id=f"checkin:{checkin.get('checkin_date')}",
        )
        events_written += 1
        timeline.append({"type": "mood", "at": checkin.get("checkin_date"), "signals": mood_sig})

    sessions_meta = list_user_sessions(user_id, session_limit)
    for meta in reversed(sessions_meta):
        state = load_session(meta["session_id"])
        if not state:
            continue
        stages["counseling"] = True
        text = _messages_blob(state.messages)
        tarot_sig = extract_tarot_signals(state.tarot_handoff)
        if tarot_sig:
            stages["tarot_exploration"] = True
        session_scores = aggregate_domain_scores(
            tarot_signals=tarot_sig,
            mood_signals=mood_dimension_scores(checkins[:1]) if checkins else {},
            text=text,
            formal_answers=state.formal_answers,
        )
        domain_scores = merge_spectrum_scores(domain_scores, session_scores)
        recs = recommendations_from_spectra(session_scores)
        for item in recs.get("instruments") or []:
            tracked_inst.add(item["instrument_id"])
        for item in recs.get("techniques") or []:
            tracked_tech.add(item["technique"])
        record_event(
            user_id,
            "counseling_session",
            {
                "session_id": state.session_id,
                "domain_scores": session_scores,
                "backfill": True,
                "turn_count": state.turn_count,
            },
            event_at=meta.get("updated_at"),
            source_id=f"session:{state.session_id}",
        )
        events_written += 1
        timeline.append({"type": "counseling", "at": meta.get("updated_at"), "signals": session_scores})

    recs = recommendations_from_spectra(domain_scores)
    if recs.get("instruments") or recs.get("techniques"):
        stages["recommendations"] = True

    profile = {
        "user_id": user_id,
        "domain_scores": domain_scores,
        "recommendations": recs,
        "pipeline_stages": stages,
        "tracked_instruments": sorted(tracked_inst),
        "tracked_techniques": sorted(tracked_tech),
        "backfill_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "backfill_stats": {
            "events_written": events_written,
            "tarot_draws": len(draws),
            "checkins": len(checkins),
            "sessions": len(sessions_meta),
        },
        "timeline_preview": sorted(timeline, key=lambda x: x.get("at") or "")[-12:],
    }
    profile["pipeline_status"] = build_pipeline_status(profile)
    profile["recent_events"] = list_events(user_id, 20)
    save_profile(user_id, profile)
    return profile


def get_user_psych_profile(user_id: str, *, auto_backfill: bool = True) -> Dict[str, Any]:
    profile = load_profile(user_id)
    if profile is None and auto_backfill:
        profile = backfill_user_profile(user_id)
    elif profile is not None:
        profile["pipeline_status"] = build_pipeline_status(profile)
        profile.setdefault("recent_events", list_events(user_id, 15))
    if profile is None:
        return {
            "user_id": user_id,
            "empty": True,
            "disclaimer": "스크리닝·웰니스 참고용이며 DSM-5 진단·의료행위가 아닙니다.",
            "pipeline_status": build_pipeline_status({}),
        }
    profile["disclaimer"] = "스크리닝·웰니스 참고용이며 DSM-5 진단·의료행위가 아닙니다."
    return profile
