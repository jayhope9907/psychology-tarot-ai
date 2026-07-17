"""DSM-5 다차원 통합 내재화(Internalizing) 스펙트럼 엔진 (비진단 참고 지표).

파편화된 개별 검사 대신 실시간 미세 행동 데이터(타이핑 망설임, 백스페이스,
낱말카드 취소, 반응 지연)와 보정된 체크인 지표를 통합 연산한다.

모든 출력은 웰니스 참고 지표이며 진단이 아니다 (non_diagnostic).
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class UnifiedEmotionalSpectrumEngine:
    """내재화 스펙트럼 통합 연산 엔진.

    우울·불안·강박·공황·조울 순환 고리와 와해성(사고 이탈) 신호를
    선형 결합 + 공병(Comorbidity) 시너지 항으로 통합한다.
    """

    def __init__(self) -> None:
        # 임상적 공병(Comorbidity) 시너지 가중치 상숫값
        self.beta_depression_anxiety = 1.4  # 우울·불안 결합 증폭 계수
        self.beta_ocd_panic = 1.3           # 강박적 통제가 공황으로 무너질 때의 계수

    def calculate_internalizing_spectrum(
        self,
        base_scores: Dict[str, float],
        behavioral_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """우울, 강박, 공황, 조울 4대 순환 고리와 와해성 신호를 통합 연산."""
        # 1. 기초 범주별 normalized 지표 (0.0 ~ 1.0)
        d_dep = min(max(base_scores.get("depressive", 0.0) / 100.0, 0.0), 1.0)
        d_anx = min(max(base_scores.get("anxiety", 0.0) / 100.0, 0.0), 1.0)
        d_som = min(max(base_scores.get("somatic", 0.0) / 100.0, 0.0), 1.0)

        # 2. 미세 행동 데이터(타이핑 망설임, 낱말카드 취소) 기반 강박·공황 정밀 보정
        hesitation_idx = float(behavioral_metrics.get("hesitation_index", 0.0) or 0.0)
        hesitation_idx = min(max(hesitation_idx, 0.0), 1.0)
        backspace_cnt = int(behavioral_metrics.get("backspace_count", 0) or 0)

        # 인지적 과다 통제(강박) 지수
        d_ocd = min(d_anx * 0.5 + (hesitation_idx * 0.3) + (min(backspace_cnt, 20) / 20.0) * 0.2, 1.0)

        # 특정 단어 지연 반응(Reaction Time) 기반 공황 지수
        delay_ms = float(behavioral_metrics.get("word_delay_ms", 0) or 0)
        d_pan = min(d_anx * 0.4 + (min(delay_ms, 5000) / 5000.0) * 0.6, 1.0)

        # 3. 조울(Bipolar) 감정 진동 폭(Variance)
        history_variance = float(behavioral_metrics.get("mood_history_variance", 0.0) or 0.0)
        history_variance = min(max(history_variance, 0.0), 1.0)
        d_bip = min(d_dep * 0.3 + (history_variance * 0.7), 1.0)

        # 4. 와해성 신호 분석 (연상 이완 및 마인드맵 파편화) — 참고 지표
        loose_assoc = float(behavioral_metrics.get("loose_association_score", 0.0) or 0.0)
        loose_assoc = min(max(loose_assoc, 0.0), 1.0)
        ego_loss = float(behavioral_metrics.get("ego_boundary_loss_score", 0.0) or 0.0)
        ego_loss = min(max(ego_loss, 0.0), 1.0)

        sch_spectrum = {
            "loose_association": round(loose_assoc * 100, 1),
            "thought_blocking": round(min(hesitation_idx * 1.5, 1.0) * 100, 1),
            "ego_boundary_loss": round(ego_loss * 100, 1),
            "delusional_affinity": round(max(loose_assoc, ego_loss) * 90, 1),
        }
        sch_total_avg = (loose_assoc + ego_loss) / 2.0

        # 5. 내재화 총합 지수: 선형 결합 + 상호작용 공병 시너지
        linear_sum = (d_dep * 0.3) + (d_anx * 0.25) + (d_ocd * 0.25) + (d_pan * 0.2)
        interaction_term = (
            self.beta_depression_anxiety * (d_dep * d_anx)
            + self.beta_ocd_panic * (d_ocd * d_pan)
        )
        total_internalizing = min((linear_sum + interaction_term * 0.4) * 100, 100.0)

        # 6. 내재화 참고 경고 레벨 (겉은 멀쩡해 보여도 속이 타는 고위험군 신호)
        if total_internalizing >= 80.0:
            risk_level = "HIGH_ALERT"
        elif total_internalizing >= 50.0:
            risk_level = "MONITOR"
        else:
            risk_level = "NORMAL"

        # 7. 와해성/고위험 신호 시 지지형 안전 기지 접근으로 강제 스위칭
        suggested_agent = (
            "SUNG_AH_SUPPORT"
            if (sch_total_avg > 0.6 or risk_level == "HIGH_ALERT")
            else "PROST_CONFRONTATION"
        )

        return {
            "total_internalizing_score": round(total_internalizing, 1),
            "internalizing_risk_level": risk_level,
            "suggested_approach": suggested_agent,
            "dimensions": {
                "depressive_index": round(d_dep * 100, 1),
                "anxiety_index": round(d_anx * 100, 1),
                "obsessive_compulsive": round(d_ocd * 100, 1),
                "panic_index": round(d_pan * 100, 1),
                "bipolar_fluctuation_index": round(d_bip * 100, 1),
                "somatic_symptom_index": round(d_som * 100, 1),
                "schizophrenia_spectrum": sch_spectrum,
            },
            "non_diagnostic": True,
        }


_ENGINE = UnifiedEmotionalSpectrumEngine()

APPROACH_LABELS_KO = {
    "SUNG_AH_SUPPORT": "지지·안전 기지 모드",
    "PROST_CONFRONTATION": "탐색·직면 모드",
}


def resolve_base_scores_from_sanitized(sanitized: Optional[Mapping[str, Any]]) -> Dict[str, float]:
    """보정된 체크인 가중치(0-100) → 기초 범주 지표 프록시.

    mood가 낮을수록 우울 프록시↑, energy가 낮을수록 신체화 프록시↑.
    """
    weights = dict((sanitized or {}).get("initialWeights") or {})

    def _w(key: str) -> float:
        try:
            return min(max(float(weights.get(key, 50)), 0.0), 100.0)
        except (TypeError, ValueError):
            return 50.0

    return {
        "depressive": 100.0 - _w("mood"),
        "anxiety": _w("anxiety"),
        "somatic": 100.0 - _w("energy"),
    }


def resolve_behavioral_metrics(
    state: Any,
    client_metrics: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """클라이언트 미세 행동 데이터 + 서버 파생 지표 병합."""
    merged: Dict[str, Any] = {}
    allowed = (
        "hesitation_index",
        "backspace_count",
        "word_delay_ms",
        "word_card_cancel_count",
        "mood_history_variance",
        "loose_association_score",
        "ego_boundary_loss_score",
    )
    for key in allowed:
        val = (client_metrics or {}).get(key)
        if val is not None:
            merged[key] = val

    # 낱말카드 취소 횟수는 망설임 지수에 가산 (과다 통제 신호)
    cancels = int(merged.get("word_card_cancel_count", 0) or 0)
    if cancels:
        base_hes = float(merged.get("hesitation_index", 0.0) or 0.0)
        merged["hesitation_index"] = min(base_hes + min(cancels, 10) / 10.0 * 0.3, 1.0)

    # 서버 파생: 감정 변동 폭 (emotional pattern SUD 시계열)
    if "mood_history_variance" not in merged:
        try:
            from app.services.emotional_pattern import analyze_personal_pattern

            analysis = analyze_personal_pattern(getattr(state, "user_id", ""), window=8) or {}
            trend = analysis.get("trend") or {}
            var = trend.get("variance") or trend.get("distressVariance")
            if var is not None:
                merged["mood_history_variance"] = min(max(float(var) / 25.0, 0.0), 1.0)
        except Exception:
            pass

    # 서버 파생: 마인드맵 파편화 → 자아 경계 프록시 (경계 점수가 낮을수록 깊은 층 신호↑)
    if "ego_boundary_loss_score" not in merged:
        try:
            wc = (getattr(state, "phase_notes", None) or {}).get("word_card_analysis") or {}
            score = wc.get("boundaryScore")
            if score is not None:
                merged["ego_boundary_loss_score"] = min(max(1.0 - float(score), 0.0), 1.0) * 0.6
        except Exception:
            pass

    return merged


def compute_emotional_spectrum(
    *,
    state: Any = None,
    sanitized: Optional[Mapping[str, Any]] = None,
    behavioral_metrics: Optional[Mapping[str, Any]] = None,
    base_scores: Optional[Mapping[str, float]] = None,
) -> Dict[str, Any]:
    """세션 상태 기반 통합 스펙트럼 계산 (엔진 단일 진입점)."""
    scores = dict(base_scores) if base_scores else resolve_base_scores_from_sanitized(sanitized)
    metrics = resolve_behavioral_metrics(state, behavioral_metrics) if state is not None else dict(
        behavioral_metrics or {}
    )
    result = _ENGINE.calculate_internalizing_spectrum(scores, metrics)
    result["baseScores"] = {k: round(float(v), 1) for k, v in scores.items()}
    result["behavioralMetrics"] = metrics
    result["approachLabelKo"] = APPROACH_LABELS_KO.get(result["suggested_approach"], "")
    result["mind_room"] = parse_clinical_state_to_room(result)
    return result


def parse_clinical_state_to_room(result: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """스펙트럼 상태 → '마음의 방' 레이아웃 파라미터 (프론트 시각화 계약).

    - 와해성 신호 폭발: 방 레이아웃 파편화 왜곡 + 지지형 페르소나 강제 스위칭
    - 내재화 고위험(강박성 우울·억압): 차갑고 딱딱한 대칭의 고립된 방
    - 안정: 따뜻하고 인간미 넘치는 노란 방
    """
    doc = dict(result or {})
    dims = doc.get("dimensions") or {}
    sch = dims.get("schizophrenia_spectrum") or {}
    sch_total = (
        float(sch.get("loose_association", 0.0) or 0.0)
        + float(sch.get("ego_boundary_loss", 0.0) or 0.0)
    ) / 2.0
    total = float(doc.get("total_internalizing_score") or 0.0)

    if sch_total > 60.0:
        return {
            "color_tone": "fractured-distorted",
            "lighting_level": 30,
            "wall_symmetry": "broken",
            # 자극 방지: 지지형 안전 기지 페르소나 강제 스위칭
            "agent_persona": "SUNG_AH_SUPPORT",
        }

    if total >= 80.0:
        return {
            "color_tone": "dark-gray",
            "lighting_level": 15,  # 극도의 어둠과 무기력
            "wall_symmetry": "rigid",  # 강박적 정렬
            "agent_persona": str(doc.get("suggested_approach") or "SUNG_AH_SUPPORT"),
        }

    return {
        "color_tone": "warm-yellow",
        "lighting_level": 85,
        "wall_symmetry": "natural",
        "agent_persona": "SUNG_AH_SUPPORT",
    }


def build_spectrum_prompt_block(result: Optional[Mapping[str, Any]]) -> str:
    """스펙트럼 결과 → 시스템 프롬프트 지침 (내담자에게 수치·라벨 노출 금지)."""
    if not result:
        return ""
    risk = str(result.get("internalizing_risk_level") or "NORMAL")
    approach = str(result.get("suggested_approach") or "PROST_CONFRONTATION")
    if risk == "NORMAL" and approach != "SUNG_AH_SUPPORT":
        return ""

    lines = [
        "## 내재화 스펙트럼 신호 (내부 참고 — 내담자에게 수치·범주명 절대 언급 금지)",
        f"- 내부 위험 신호: {risk} / 권장 접근: {approach}",
    ]
    if approach == "SUNG_AH_SUPPORT":
        lines.extend(
            [
                "- 지지·안전 기지 모드로 전환하세요: 직면·과제 제안을 멈추고, 짧고 따뜻한 반영과 안정화(호흡·현재 감각)만 사용하세요.",
                "- 논리적 분석이나 사고 교정 시도 금지. 내담자의 속도를 그대로 따라가세요.",
                "- 위기 신호가 이어지면 전문 기관(1393 등) 안내를 부드럽게 한 번만 덧붙이세요.",
            ]
        )
    else:
        lines.append("- 주의 깊게 관찰하되 평소의 따뜻한 탐색 톤을 유지하세요.")
    lines.append("- 진단명·검사 점수를 내담자에게 말하지 마세요. 모든 지표는 비진단 참고용입니다.")
    return "\n".join(lines)
