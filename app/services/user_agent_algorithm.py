"""유저별 고유 AI 에이전트 지문(fingerprint) · 패턴 알고리즘 · 종단 추적."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.models.clinical import ClinicalSchool
from app.services.psych_timeline import list_events, load_profile, record_event, save_profile

FINGERPRINT_VERSION = "1.0.0"
EMA_ALPHA = 0.28  # 최근 턴 가중

QUANT_KEYS = (
    "psychological_readiness_index",
    "tree_energy_index",
    "psychiatric_stress_weight",
    "attachment_matrix_score",
)

PATTERN_LABELS_KO = {
    "recurring_distortion": "반복되는 생각 패턴",
    "mood_decline_streak": "기분 하락 연속",
    "spectrum_persistence": "스펙트럼 지속 신호",
    "phase_stall": "상담 단계 정체",
    "high_stress_cluster": "스트레스 군집",
    "relational_loop": "관계 테마 반복",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _algo_id(user_id: str) -> str:
    digest = hashlib.sha256(f"agent-algo:{user_id}".encode("utf-8")).hexdigest()
    return f"ALG-{digest[:10].upper()}"


def empty_fingerprint(user_id: str = "") -> Dict[str, Any]:
    return {
        "version": FINGERPRINT_VERSION,
        "algo_id": _algo_id(user_id) if user_id else "ALG-NEW",
        "sample_turns": 0,
        "school_priors": {},
        "quant_ema": {k: 0.5 for k in QUANT_KEYS},
        "distortion_hist": {},
        "mood_hist": {},
        "theme_hist": {},
        "phase_hist": {},
        "persona_reason_counts": {},
        "assessment_hist": {},
        "psychometric_profile": {},
        "last_school": None,
        "confidence": 0.0,
        "updated_at": None,
        "created_at": _utc_now(),
    }


def _ema(prev: float, new: float, alpha: float = EMA_ALPHA) -> float:
    return round((1 - alpha) * float(prev) + alpha * float(new), 4)


def _bump_hist(hist: Dict[str, Any], key: Optional[str], weight: float = 1.0) -> None:
    if not key:
        return
    hist[key] = round(float(hist.get(key) or 0) + weight, 3)


def _normalize_priors(priors: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(0.0, float(v)) for v in priors.values()) or 1.0
    return {k: round(max(0.0, float(v)) / total, 4) for k, v in priors.items()}


def evolve_fingerprint(
    user_id: str,
    *,
    persona_routing: Optional[Dict[str, Any]] = None,
    quant_features: Optional[Dict[str, Any]] = None,
    counseling_phase: Optional[str] = None,
    message_themes: Optional[List[str]] = None,
    profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """세션 턴 신호를 EMA로 흡수해 유저 고유 알고리즘 지문을 갱신."""
    profile = profile if profile is not None else (load_profile(user_id) or {"user_id": user_id})
    fp = dict(profile.get("agent_fingerprint") or empty_fingerprint(user_id))
    if not fp.get("algo_id") or fp.get("algo_id") == "ALG-NEW":
        fp["algo_id"] = _algo_id(user_id)
    fp.setdefault("version", FINGERPRINT_VERSION)
    fp.setdefault("school_priors", {})
    fp.setdefault("quant_ema", {k: 0.5 for k in QUANT_KEYS})
    fp.setdefault("distortion_hist", {})
    fp.setdefault("mood_hist", {})
    fp.setdefault("theme_hist", {})
    fp.setdefault("phase_hist", {})
    fp.setdefault("persona_reason_counts", {})
    fp.setdefault("assessment_hist", {})
    fp.setdefault("psychometric_profile", {})
    fp.setdefault("created_at", _utc_now())

    routing = persona_routing or {}
    quant = quant_features or {}
    school = routing.get("school")
    mood = routing.get("mood_state")
    reason = routing.get("reason")
    distortions = routing.get("detected_distortions") or []

    if school:
        priors = dict(fp.get("school_priors") or {})
        priors[school] = float(priors.get(school) or 0) + 1.0
        # decay soft: keep relative by normalizing later
        fp["school_priors"] = _normalize_priors({k: v * 0.92 for k, v in priors.items()})
        # re-add current school weight after decay
        boosted = dict(fp["school_priors"])
        boosted[school] = float(boosted.get(school) or 0) + 0.18
        fp["school_priors"] = _normalize_priors(boosted)
        fp["last_school"] = school

    ema = dict(fp.get("quant_ema") or {})
    for key in QUANT_KEYS:
        raw = quant.get(key)
        if isinstance(raw, (int, float)):
            ema[key] = _ema(float(ema.get(key) or 0.5), float(raw))
    fp["quant_ema"] = ema

    for d in distortions:
        _bump_hist(fp["distortion_hist"], d)
    _bump_hist(fp["mood_hist"], mood)
    _bump_hist(fp["phase_hist"], counseling_phase)
    _bump_hist(fp["persona_reason_counts"], reason)
    for theme in message_themes or []:
        _bump_hist(fp["theme_hist"], theme)

    turns = int(fp.get("sample_turns") or 0) + 1
    fp["sample_turns"] = turns
    fp["confidence"] = round(min(0.95, 0.12 + turns * 0.04), 3)
    fp["updated_at"] = _utc_now()
    fp["algorithm_summary_ko"] = summarize_fingerprint(fp)

    profile["agent_fingerprint"] = fp
    profile["user_id"] = user_id
    return profile


def extract_message_themes(text: str) -> List[str]:
    blob = (text or "").lower()
    rules = {
        "work": ("직장", "회사", "상사", "업무", "야근", "동료"),
        "relationship": ("연인", "애인", "배우자", "이별", "관계", "가족", "부모"),
        "self_worth": ("자존", "못난", "쓸모", "비교", "실패"),
        "anxiety": ("불안", "걱정", "초조", "긴장", "공황"),
        "depression": ("우울", "무기력", "허무", "공허", "우울해"),
        "sleep": ("잠", "불면", "수면", "새벽"),
        "money": ("돈", "빚", "월급", "생활비", "경제"),
        "substance": (
            "술",
            "담배",
            "마약",
            "중독",
            "갈망",
            "재발",
            "단주",
            "단약",
            "금단",
            "약물",
            "대마",
            "필로폰",
            "과음",
        ),
    }
    hits = [name for name, kws in rules.items() if any(k in blob for k in kws)]
    return hits[:6]


def detect_user_patterns(
    user_id: str,
    *,
    fingerprint: Optional[Dict[str, Any]] = None,
    profile: Optional[Dict[str, Any]] = None,
    event_limit: int = 40,
) -> List[Dict[str, Any]]:
    """종단 이벤트·지문 기반 패턴 탐지 (비진단)."""
    profile = profile if profile is not None else (load_profile(user_id) or {})
    fp = fingerprint or profile.get("agent_fingerprint") or empty_fingerprint(user_id)
    events = list_events(user_id, event_limit)
    patterns: List[Dict[str, Any]] = []

    dist_hist = fp.get("distortion_hist") or {}
    top_dist = sorted(dist_hist.items(), key=lambda x: -x[1])
    if top_dist and top_dist[0][1] >= 3:
        key, count = top_dist[0]
        patterns.append(
            {
                "pattern_id": "recurring_distortion",
                "label_ko": PATTERN_LABELS_KO["recurring_distortion"],
                "confidence": round(min(0.95, 0.35 + count * 0.08), 3),
                "evidence": {"distortion": key, "count": count},
                "guidance_ko": "같은 생각 틀이 반복되고 있어요. 대화에서 부드럽게 알아차리게 돕습니다.",
            }
        )

    mood_events = [e for e in events if e.get("event_type") == "mood_checkin"]
    scores: List[float] = []
    for e in mood_events[:8]:
        payload = e.get("payload") or e.get("payload_json") or {}
        if isinstance(payload, str):
            continue
        ms = payload.get("mood_score")
        if isinstance(ms, (int, float)):
            scores.append(float(ms))
    if len(scores) >= 3 and all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1)):
        patterns.append(
            {
                "pattern_id": "mood_decline_streak",
                "label_ko": PATTERN_LABELS_KO["mood_decline_streak"],
                "confidence": 0.72,
                "evidence": {"recent_mood_scores": scores[:5]},
                "guidance_ko": "최근 체크인 기분이 내려가는 흐름입니다. 페이스를 천천히, 안전 안내를 우선합니다.",
            }
        )

    domain = profile.get("domain_scores") or {}
    persistent = sorted(
        ((k, float(v)) for k, v in domain.items() if isinstance(v, (int, float)) and float(v) >= 0.55),
        key=lambda x: -x[1],
    )[:3]
    if persistent:
        patterns.append(
            {
                "pattern_id": "spectrum_persistence",
                "label_ko": PATTERN_LABELS_KO["spectrum_persistence"],
                "confidence": round(min(0.9, 0.4 + persistent[0][1] * 0.4), 3),
                "evidence": {"top_spectra": [{"id": k, "score": round(v, 3)} for k, v in persistent]},
                "guidance_ko": "특정 마음 영역 신호가 지속됩니다. 강제 진단 없이 탐색 우선순위에 반영합니다.",
            }
        )

    phase_hist = fp.get("phase_hist") or {}
    if phase_hist:
        top_phase, pcount = max(phase_hist.items(), key=lambda x: x[1])
        if pcount >= 4 and top_phase in ("rapport", "exploration", "PHASE_RAPPORT", "관계 형성"):
            patterns.append(
                {
                    "pattern_id": "phase_stall",
                    "label_ko": PATTERN_LABELS_KO["phase_stall"],
                    "confidence": 0.6,
                    "evidence": {"phase": top_phase, "count": pcount},
                    "guidance_ko": "같은 상담 단계에 머무는 경향이 있어요. 작은 다음 스텝을 제안합니다.",
                }
            )

    stress = float((fp.get("quant_ema") or {}).get("psychiatric_stress_weight") or 0)
    readiness = float((fp.get("quant_ema") or {}).get("psychological_readiness_index") or 0.5)
    if stress >= 0.62 and readiness <= 0.45:
        patterns.append(
            {
                "pattern_id": "high_stress_cluster",
                "label_ko": PATTERN_LABELS_KO["high_stress_cluster"],
                "confidence": 0.78,
                "evidence": {"stress_ema": stress, "readiness_ema": readiness},
                "guidance_ko": "스트레스가 높고 준비도가 낮아 보입니다. 짧은 확인·안정화 톤을 우선합니다.",
            }
        )

    themes = fp.get("theme_hist") or {}
    if float(themes.get("relationship") or 0) >= 3:
        patterns.append(
            {
                "pattern_id": "relational_loop",
                "label_ko": PATTERN_LABELS_KO["relational_loop"],
                "confidence": 0.7,
                "evidence": {"relationship_mentions": themes.get("relationship")},
                "guidance_ko": "관계 이야기가 반복됩니다. 관계·경계·욕구 탐색을 에이전트 렌즈에 반영합니다.",
            }
        )

    patterns.sort(key=lambda p: -float(p.get("confidence") or 0))
    return patterns[:8]


def summarize_fingerprint(fp: Dict[str, Any]) -> str:
    priors = fp.get("school_priors") or {}
    top_school = max(priors.items(), key=lambda x: x[1])[0] if priors else "INTEGRATIVE"
    dist = fp.get("distortion_hist") or {}
    top_dist = max(dist.items(), key=lambda x: x[1])[0] if dist else None
    conf = fp.get("confidence") or 0
    parts = [
        f"고유 알고리즘 {fp.get('algo_id')}",
        f"선호 렌즈 {top_school}",
        f"신뢰도 {int(conf * 100)}%",
        f"샘플 {fp.get('sample_turns') or 0}턴",
    ]
    if top_dist:
        parts.append(f"반복 패턴 {top_dist}")
    return " · ".join(parts)


def top_school_from_fingerprint(fp: Dict[str, Any]) -> Optional[ClinicalSchool]:
    priors = fp.get("school_priors") or {}
    if not priors:
        return None
    best = max(priors.items(), key=lambda x: x[1])
    if best[1] < 0.22:
        return None
    try:
        return ClinicalSchool(best[0])
    except ValueError:
        return None


def apply_fingerprint_bias(
    routing: Dict[str, Any],
    fingerprint: Optional[Dict[str, Any]],
    *,
    user_explicit: bool = False,
) -> Dict[str, Any]:
    """명시 선택이 없을 때 지문 prior로 학파를 부드럽게 보정."""
    if user_explicit or not fingerprint:
        return routing
    conf = float(fingerprint.get("confidence") or 0)
    if conf < 0.25:
        return routing
    prior_school = top_school_from_fingerprint(fingerprint)
    if not prior_school:
        return routing
    current = routing.get("school")
    current_val = current.value if hasattr(current, "value") else current
    priors = fingerprint.get("school_priors") or {}
    prior_w = float(priors.get(prior_school.value) or 0)
    cur_w = float(priors.get(str(current_val)) or 0)
    if prior_w >= cur_w + 0.12 and prior_w >= 0.28:
        from app.services.counseling_theories import get_theory_meta

        meta = get_theory_meta(prior_school)
        out = dict(routing)
        out["school"] = prior_school
        out["reason"] = "user_agent_fingerprint_prior"
        out["persona_label"] = meta["label"]
        out["persona_subtitle"] = meta.get("subtitle")
        out["counselor_tone"] = meta.get("counselor_tone")
        out["techniques"] = meta.get("techniques")
        out["category"] = meta.get("category")
        out["fingerprint_bias"] = True
        return out
    return routing


def seed_quant_from_fingerprint(
    quant: Dict[str, Any],
    fingerprint: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """지문 EMA를 현재 턴 quant에 혼합해 프롬프트 바인딩을 안정화."""
    if not fingerprint:
        return quant
    ema = fingerprint.get("quant_ema") or {}
    conf = float(fingerprint.get("confidence") or 0)
    mix = min(0.55, conf)
    out = dict(quant or {})
    for key in QUANT_KEYS:
        if key not in ema:
            continue
        cur = out.get(key)
        if isinstance(cur, (int, float)):
            out[key] = round((1 - mix) * float(cur) + mix * float(ema[key]), 4)
        else:
            out[key] = float(ema[key])
    out["agent_algo_id"] = fingerprint.get("algo_id")
    out["agent_confidence"] = conf
    return out


def absorb_assessments_into_fingerprint(user_id: str, session: Any, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """formal_answers 점수를 에이전트 지문에 자동 저장·동기화해 유저를 입체화."""
    from app.assessments import ALL_INSTRUMENTS

    profile = profile if profile is not None else (load_profile(user_id) or {"user_id": user_id})
    fp = dict(profile.get("agent_fingerprint") or empty_fingerprint(user_id))
    fp.setdefault("assessment_hist", {})
    fp.setdefault("psychometric_profile", {})
    psych = dict(fp.get("psychometric_profile") or {})
    signals = dict(psych.get("abnormal_signals") or {})
    hist = dict(fp.get("assessment_hist") or {})

    formal = getattr(session, "formal_answers", None) or {}
    for instrument_id, answers in formal.items():
        if instrument_id not in ALL_INSTRUMENTS or not isinstance(answers, dict):
            continue
        scored = ALL_INSTRUMENTS[instrument_id].score_partial(answers)
        hist[instrument_id] = {
            "completed_items": scored.get("completed_items"),
            "completion_rate": scored.get("completion_rate"),
            "severity_hint": scored.get("severity_hint"),
            "partial_score": scored.get("partial_score"),
            "updated_at": _utc_now(),
        }
        if instrument_id == "mbti_preference":
            psych["mbti"] = {
                "type_code_hint": scored.get("type_code_hint"),
                "preference_leanings": scored.get("preference_leanings"),
                "non_diagnostic": True,
            }
        elif instrument_id.endswith("_probe") or instrument_id in (
            "phq9", "gad7", "isi", "pss", "pcl5", "rses", "attachment_ecr",
        ):
            signals[instrument_id] = {
                "severity_hint": scored.get("severity_hint"),
                "signal_ratio": scored.get("signal_ratio"),
                "partial_score": scored.get("partial_score"),
                "non_diagnostic": True,
            }

    psych["abnormal_signals"] = signals
    psych["synced_at"] = _utc_now()
    fp["assessment_hist"] = hist
    fp["psychometric_profile"] = psych
    fp["updated_at"] = _utc_now()
    fp["algorithm_summary_ko"] = summarize_fingerprint(fp)
    profile["agent_fingerprint"] = fp
    profile["user_id"] = user_id
    return profile


def fingerprint_prompt_block(fingerprint: Optional[Dict[str, Any]], patterns: Optional[List[Dict[str, Any]]] = None) -> str:
    if not fingerprint or int(fingerprint.get("sample_turns") or 0) < 1:
        # still allow psychometric-only profiles
        psych = (fingerprint or {}).get("psychometric_profile") or {}
        if not psych.get("mbti") and not psych.get("abnormal_signals"):
            return ""
    lines = [
        "\n\n## [유저 고유 에이전트 알고리즘 — 참고용·비진단]",
        f"- 알고리즘 ID: {(fingerprint or {}).get('algo_id')}",
        f"- 요약: {(fingerprint or {}).get('algorithm_summary_ko') or summarize_fingerprint(fingerprint or {})}",
        f"- 신뢰도: {(fingerprint or {}).get('confidence')}",
    ]
    ema = (fingerprint or {}).get("quant_ema") or {}
    if ema:
        lines.append(
            "- 개인화 지표(EMA): "
            + ", ".join(f"{k}={ema.get(k)}" for k in QUANT_KEYS if k in ema)
        )
    psych = (fingerprint or {}).get("psychometric_profile") or {}
    mbti = psych.get("mbti") or {}
    if mbti.get("type_code_hint"):
        lines.append(f"- MBTI 선호 힌트(교육용·비진단): {mbti.get('type_code_hint')}")
    signals = psych.get("abnormal_signals") or {}
    elevated = [k for k, v in signals.items() if isinstance(v, dict) and v.get("severity_hint") in ("elevated", "mild", "moderate")]
    if elevated:
        lines.append("- 탐색 신호 영역: " + ", ".join(elevated[:5]))
        lines.append("- 위 영역은 진단이 아닙니다. 관찰·공감 문장으로만 부드럽게 확인하세요.")
    if patterns:
        top = patterns[:3]
        lines.append("- 감지된 패턴: " + "; ".join(f"{p.get('label_ko')}({p.get('confidence')})" for p in top))
        lines.append("- 패턴은 자기이해 참고용이며 진단이 아닙니다. 강요하지 마세요.")
    lines.append(
        "- 기분·대인관계를 물을 때: 「제가 봤을 때는 현재 감정이나 하고 있는 일에 많이 힘들어 보이시네요」처럼 "
        "관찰로 풀어 주세요. 설문형 연속 질문 금지."
    )
    lines.append("- 이전과 같은 문장을 반복하지 말고, 이 유저의 고유 패턴에 맞춰 한 단계 깊게 반응하세요.")
    return "\n".join(lines)


def sync_user_agent_from_session(user_id: str, session: Any) -> Dict[str, Any]:
    """상담 동기화 시 지문·패턴을 프로필에 저장하고 타임라인에 스냅샷."""
    themes = extract_message_themes(
        " ".join((m.get("content") or "") for m in (session.messages or [])[-6:] if m.get("role") == "user")
    )
    profile = evolve_fingerprint(
        user_id,
        persona_routing=session.persona_routing,
        quant_features=session.quant_features,
        counseling_phase=getattr(session, "counseling_phase", None),
        message_themes=themes,
    )
    profile = absorb_assessments_into_fingerprint(user_id, session, profile=profile)
    fp = profile["agent_fingerprint"]
    patterns = detect_user_patterns(user_id, fingerprint=fp, profile=profile)
    profile["pattern_hits"] = patterns
    profile["agent_updated_at"] = _utc_now()
    save_profile(user_id, profile)

    record_event(
        user_id,
        "agent_fingerprint_tick",
        {
            "algo_id": fp.get("algo_id"),
            "sample_turns": fp.get("sample_turns"),
            "confidence": fp.get("confidence"),
            "school_priors": fp.get("school_priors"),
            "quant_ema": fp.get("quant_ema"),
            "psychometric_profile": fp.get("psychometric_profile"),
            "patterns": [{"pattern_id": p["pattern_id"], "confidence": p["confidence"]} for p in patterns[:5]],
            "non_diagnostic": True,
        },
        source_id=f"agent:{session.session_id}:{fp.get('sample_turns')}",
    )
    return {
        "agent_fingerprint": fp,
        "patterns": patterns,
        "profile": profile,
    }


def sync_agent_after_assessment(
    user_id: str,
    session: Any,
    *,
    instrument: Optional[str] = None,
    item_id: Optional[str] = None,
) -> Dict[str, Any]:
    """검사 응답 직후 에이전트에 자동 저장·동기화."""
    profile = absorb_assessments_into_fingerprint(user_id, session)
    # ensure algo id exists even before chat turns
    fp = profile["agent_fingerprint"]
    if not fp.get("algo_id") or fp.get("algo_id") == "ALG-NEW":
        fp["algo_id"] = _algo_id(user_id)
    if int(fp.get("sample_turns") or 0) < 1:
        fp["sample_turns"] = 1
        fp["confidence"] = max(float(fp.get("confidence") or 0), 0.2)
    fp["algorithm_summary_ko"] = summarize_fingerprint(fp)
    patterns = detect_user_patterns(user_id, fingerprint=fp, profile=profile)
    profile["pattern_hits"] = patterns
    profile["agent_updated_at"] = _utc_now()
    profile["agent_fingerprint"] = fp
    save_profile(user_id, profile)
    record_event(
        user_id,
        "assessment_agent_sync",
        {
            "instrument": instrument,
            "item_id": item_id,
            "algo_id": fp.get("algo_id"),
            "psychometric_profile": fp.get("psychometric_profile"),
            "non_diagnostic": True,
        },
        source_id=f"assess:{getattr(session, 'session_id', '')}:{instrument}:{item_id}",
    )
    return {
        "algo_id": fp.get("algo_id"),
        "psychometric_profile": fp.get("psychometric_profile"),
        "assessment_hist": fp.get("assessment_hist"),
        "pattern_count": len(patterns),
    }


def get_user_agent_bundle(user_id: str, *, refresh_patterns: bool = True) -> Dict[str, Any]:
    profile = load_profile(user_id) or {"user_id": user_id}
    fp = profile.get("agent_fingerprint") or empty_fingerprint(user_id)
    if not profile.get("agent_fingerprint"):
        profile["agent_fingerprint"] = fp
    patterns = profile.get("pattern_hits") or []
    if refresh_patterns:
        patterns = detect_user_patterns(user_id, fingerprint=fp, profile=profile)
        profile["pattern_hits"] = patterns
        save_profile(user_id, profile)
    events = list_events(user_id, 12)
    return {
        "user_id": user_id,
        "algo_id": fp.get("algo_id"),
        "agent_fingerprint": fp,
        "patterns": patterns,
        "pattern_count": len(patterns),
        "timeline_preview": events,
        "domain_scores": profile.get("domain_scores") or {},
        "pipeline_status": profile.get("pipeline_status"),
        "disclaimer_ko": (
            "유저 고유 알고리즘·패턴은 웰니스·자기성찰 개인화용이며 "
            "정신과 진단·치료 효과를 의미하지 않습니다."
        ),
    }


def simulate_learning_pass(user_id: str, messages: List[str]) -> Dict[str, Any]:
    """테스트 허브용: 메시지 목록으로 지문을 빠르게 학습."""
    from app.services.persona_router import route_clinical_persona
    from app.services.prompt_binding import extract_chat_quant_features
    from app.services.chat_session import ChatSessionState

    state = ChatSessionState(user_id=user_id, session_id=f"sim-{user_id[:8]}")
    for msg in messages:
        routing = route_clinical_persona(msg, None, state.messages)
        state.persona_routing = {
            "school": routing["school"].value,
            "mood_state": routing["mood_state"].value,
            "reason": routing["reason"],
            "persona_label": routing["persona_label"],
            "detected_distortions": routing["detected_distortions"],
        }
        state.quant_features = extract_chat_quant_features(msg, state)
        state.messages.append({"role": "user", "content": msg})
        state.messages.append({"role": "assistant", "content": "네, 함께 살펴볼게요."})
        state.turn_count += 1
        sync_user_agent_from_session(user_id, state)
    return get_user_agent_bundle(user_id)
