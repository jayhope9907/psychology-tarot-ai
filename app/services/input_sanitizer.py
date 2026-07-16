"""Pre-AI input gate: sanitize & compensate user payloads.

Mirrors the product contract:

  RawInputData {
    consultationMode: 'psychology' | 'faith'
    step: 1..5
    selectedCard?: string | null
    checkInMetrics?: { mood?, energy?, anxiety? }  // 0..100 preferred
  }

Before any analysis engine runs, missing tarot/check-in fields are
safely filled and faith mode isolates psychology defense fields.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Union

from app.services.consultation_mode import (
    MODE_FAITH,
    MODE_PSYCHOLOGY,
    normalize_consultation_mode,
)

DEFAULT_CHECKIN_WEIGHT = 50
ARCHETYPE_NONE = "None"
MIN_STEP = 1
MAX_STEP = 5
# Card / unconscious archetype is only trusted from step 2 onward.
CARD_TRUST_MIN_STEP = 2


def _clamp_int(value: Any, lo: int, hi: int, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def _normalize_weight(value: Any, default: int = DEFAULT_CHECKIN_WEIGHT) -> int:
    """Accept 0–100 weights, or legacy 1–5 mood/dimension scales."""
    if value is None or value == "":
        return default
    try:
        n = float(value)
    except (TypeError, ValueError):
        return default
    # Legacy home sphere axes are typically 1–5
    if 1.0 <= n <= 5.0 and n == int(n):
        # 1→0, 3→50, 5→100
        return int(round((n - 1.0) / 4.0 * 100.0))
    return _clamp_int(n, 0, 100, default)


def normalize_step(step: Any) -> int:
    return _clamp_int(step, MIN_STEP, MAX_STEP, MIN_STEP)


def safe_selected_card(step: int, selected_card: Any) -> str:
    """Step < 2 or empty card → unconscious archetype placeholder 'None'."""
    if step < CARD_TRUST_MIN_STEP:
        return ARCHETYPE_NONE
    text = str(selected_card or "").strip()
    if not text or text.lower() in {"none", "null", "undefined"}:
        return ARCHETYPE_NONE
    return text[:80]


def safe_checkin_metrics(metrics: Optional[Mapping[str, Any]]) -> Dict[str, int]:
    src = metrics or {}
    return {
        "mood": _normalize_weight(src.get("mood")),
        "energy": _normalize_weight(src.get("energy")),
        "anxiety": _normalize_weight(src.get("anxiety")),
    }


def checkin_from_mood_dimensions(
    dimensions: Optional[Mapping[str, Any]] = None,
    *,
    mood_score: Any = None,
) -> Dict[str, int]:
    """Map today's sphere check-in (1–5 dims / mood_score) → 0–100 weights."""
    dims = dimensions or {}
    mood = dims.get("valence")
    if mood is None and mood_score is not None:
        mood = mood_score
    return safe_checkin_metrics(
        {
            "mood": mood,
            "energy": dims.get("energy"),
            "anxiety": dims.get("anxiety"),
        }
    )


def sanitize_and_compensate(
    input_data: Union[Mapping[str, Any], None] = None,
    *,
    consultation_mode: Any = None,
    step: Any = None,
    selected_card: Any = None,
    check_in_metrics: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """AI 분석 엔진 직전: 유저 데이터 보완·정제 + 모드 아키텍처 격리."""
    raw = dict(input_data or {})
    mode = normalize_consultation_mode(
        consultation_mode
        if consultation_mode is not None
        else raw.get("consultationMode") or raw.get("consultation_mode")
    )
    current_step = normalize_step(
        step if step is not None else raw.get("step") or raw.get("currentStep")
    )
    card_raw = (
        selected_card
        if selected_card is not None
        else raw.get("selectedCard") or raw.get("selected_card")
    )
    metrics_raw = check_in_metrics
    if metrics_raw is None:
        metrics_raw = raw.get("checkInMetrics") or raw.get("check_in_metrics")

    safe_card = safe_selected_card(current_step, card_raw)
    safe_check_in = safe_checkin_metrics(metrics_raw if isinstance(metrics_raw, Mapping) else None)
    is_faith = mode == MODE_FAITH

    # Faith mode: disable psychology defense-mechanism channel to avoid cross-mode pollution.
    out: Dict[str, Any] = {
        "mode": mode,
        "consultationMode": mode,
        "currentStep": current_step,
        "step": current_step,
        "dominantArchetype": safe_card,
        "selectedCard": None if safe_card == ARCHETYPE_NONE else safe_card,
        "initialWeights": safe_check_in,
        "checkInMetrics": safe_check_in,
        "isFaithMode": is_faith,
        "defenseMechanismEnabled": not is_faith,
        "defenseMechanism": None if is_faith else "active",
    }
    return out


def apply_mode_isolation_to_psychodynamics(
    metrics: Optional[Mapping[str, Any]],
    *,
    consultation_mode: str,
) -> Dict[str, Any]:
    """Strip / neutralize psychology defense fields when faith mode is active."""
    from app.services.freud_jung_tracker import normalize_psychodynamic_metrics

    clean = normalize_psychodynamic_metrics(dict(metrics or {}))
    if normalize_consultation_mode(consultation_mode) == MODE_FAITH:
        clean["defense_mechanism"] = "inactive"
        clean["defenseMechanismEnabled"] = False
        clean["modeIsolated"] = True
        # Keep archetype label only if it came from a trusted card / narrative;
        # raw psychology defense taxonomy must not steer faith prompts.
    else:
        clean["defenseMechanismEnabled"] = True
        clean["modeIsolated"] = False
    clean["consultationMode"] = normalize_consultation_mode(consultation_mode) or MODE_PSYCHOLOGY
    return clean


def build_raw_input_from_session(
    state: Any,
    *,
    mood_ctx: Any = None,
    override_card: Optional[str] = None,
) -> Dict[str, Any]:
    """Assemble RawInputData from chat session + optional mood check-in context."""
    from app.services.counseling_phase import phase_index

    phase = getattr(state, "counseling_phase", None) or "rapport"
    step = phase_index(phase) + 1  # UI steps are 1..5

    card = override_card
    if card is None:
        handoff = getattr(state, "tarot_handoff", None) or {}
        if isinstance(handoff, dict):
            card = handoff.get("primary_card") or handoff.get("primaryCard")
            if not card:
                cards = handoff.get("cards") or []
                if cards and isinstance(cards[0], dict):
                    card = cards[0].get("name") or cards[0].get("id")
                elif cards:
                    card = str(cards[0])
        notes = getattr(state, "phase_notes", None) or {}
        if not card:
            card = notes.get("tarot_primary_card")

    check_in: Dict[str, Any] = {}
    if mood_ctx is not None:
        dims = getattr(mood_ctx, "dimensions", None)
        if dims is None and isinstance(mood_ctx, Mapping):
            dims = mood_ctx.get("dimensions")
            mood_score = mood_ctx.get("score") or mood_ctx.get("mood_score")
        else:
            mood_score = getattr(mood_ctx, "score", None)
        if getattr(mood_ctx, "has_checkin", False) or (
            isinstance(mood_ctx, Mapping) and mood_ctx.get("has_checkin")
        ):
            check_in = checkin_from_mood_dimensions(dims, mood_score=mood_score)

    return {
        "consultationMode": getattr(state, "consultation_mode", None) or MODE_PSYCHOLOGY,
        "step": step,
        "selectedCard": card,
        "checkInMetrics": check_in or None,
    }


def prompt_block_for_sanitized(sanitized: Mapping[str, Any]) -> str:
    """Compact system-prompt binding of compensated weights (non-diagnostic)."""
    weights = sanitized.get("initialWeights") or {}
    card = sanitized.get("dominantArchetype") or ARCHETYPE_NONE
    mode = sanitized.get("mode") or MODE_PSYCHOLOGY
    lines = [
        "## [입력 보완·정제 게이트 — 참고·비진단]",
        f"- consultationMode: {mode}",
        f"- step: {sanitized.get('currentStep')}",
        f"- dominantArchetype(card): {card}",
        (
            f"- initialWeights mood={weights.get('mood')} "
            f"energy={weights.get('energy')} anxiety={weights.get('anxiety')} "
            f"(결측 시 {DEFAULT_CHECKIN_WEIGHT} 자동 보완)"
        ),
    ]
    if sanitized.get("isFaithMode"):
        lines.append(
            "- faith 모드: 심리 방어기제 채널 비활성(defenseMechanismEnabled=false). "
            "영적 인지·임재 언어만 사용하고 프로이트식 방어기제 라벨을 내담자에게 말하지 마세요."
        )
    else:
        lines.append("- psychology 모드: 방어기제·CBT 렌즈 사용 가능(진단 단정 금지).")
    return "\n".join(lines)
