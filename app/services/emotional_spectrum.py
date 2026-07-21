"""DSM-5 다차원 통합 내재화(Internalizing) 스펙트럼 엔진 (비진단 참고 지표).

파편화된 개별 검사 대신 실시간 미세 행동 데이터(타이핑 망설임, 백스페이스,
낱말카드 취소, 반응 지연)와 보정된 체크인 지표를 통합 연산한다.

모든 출력은 웰니스 참고 지표이며 진단이 아니다 (non_diagnostic).
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class InternalizingCoreEngine:
    """내재화 핵심(InternalizingCore) 연산 엔진.

    요구사항 반영:
    - `total_internalizing_score`를 가장 먼저 계산한 뒤
    - 내부 참고 지표(디멘전/메타)를 파생
    - 70점 초과 시 다운스트림(우울/공황 트랙 리스크 + OCD/ASD 루프 디버그)까지 명시적으로 산출
    """

    def __init__(self) -> None:
        # 임상적 공병(Comorbidity) 시너지 가중치 상숫값
        self.beta_depression_anxiety = 1.4  # 우울·불안 결합 증폭 계수
        self.beta_ocd_panic = 1.3           # 강박적 통제가 공황으로 무너질 때의 계수

    def calculate_internalizing_spectrum(
        self,
        base_scores: Dict[str, float],
        behavioral_metrics: Dict[str, Any],
        *,
        defensive_language_signal: float = 0.0,
    ) -> Dict[str, Any]:
        """내재화 핵심(InternalizingCore) 연산.

        - 입력 프록시:
          1) `Gs slowdown proxy`: `word_delay_ms`
          2) `stimming proxy`: `backspace_count` + `word_card_cancel_count`
          3) `defensive language signal`: 외부(estado/persona)에서 주입되는 방어 언어 강도
        - 출력:
          - 0..100 `total_internalizing_score` (가장 먼저 산출)
          - 다운스트림 트리거(명시적 payload)
          - 기존 contract 유지용 `dimensions`
        """

        def _clamp01(x: float) -> float:
            return min(1.0, max(0.0, float(x)))

        defensive_language_signal = _clamp01(defensive_language_signal or 0.0)

        # 1) 기초 범주별 normalized 지표 (0.0 ~ 1.0)
        d_dep = _clamp01(base_scores.get("depressive", 0.0) / 100.0)
        d_anx = _clamp01(base_scores.get("anxiety", 0.0) / 100.0)
        d_som = _clamp01(base_scores.get("somatic", 0.0) / 100.0)

        # 2) 미세 행동 데이터 기반 프록시
        hesitation_idx = _clamp01(float(behavioral_metrics.get("hesitation_index", 0.0) or 0.0))
        backspace_cnt = int(behavioral_metrics.get("backspace_count", 0) or 0)
        word_card_cancel_count = int(behavioral_metrics.get("word_card_cancel_count", 0) or 0)

        # 2-1) 타이핑 지연 → Gs slowdown proxy
        delay_ms = float(behavioral_metrics.get("word_delay_ms", 0) or 0)
        gs_slowdown_proxy = _clamp01(min(delay_ms, 5000.0) / 5000.0)

        # 2-2) 반복/취소 → stimming proxy
        stimming_proxy = _clamp01((min(backspace_cnt, 50) / 50.0) * 0.7 + (min(word_card_cancel_count, 10) / 10.0) * 0.3)

        # 3) 방어 언어 신호 → 불안 코어에 소폭 가중
        # (기본값 defensive_language_signal=0이면 기존 산식과 동일)
        d_anx_eff = _clamp01(d_anx + defensive_language_signal * 0.15)

        # 3-1) 인지적 과다 통제(강박) 지수
        d_ocd = min(d_anx_eff * 0.5 + (hesitation_idx * 0.3) + (min(backspace_cnt, 20) / 20.0) * 0.2, 1.0)

        # 3-2) 특정 단어 지연 반응(Reaction Time) 기반 공황 지수
        d_pan = min(d_anx_eff * 0.4 + (min(delay_ms, 5000.0) / 5000.0) * 0.6, 1.0)

        # 4) 조울(Bipolar) 감정 진동 폭(Variance)
        history_variance = _clamp01(float(behavioral_metrics.get("mood_history_variance", 0.0) or 0.0))
        d_bip = min(d_dep * 0.3 + (history_variance * 0.7), 1.0)

        # 5) 와해성 신호 분석 (연상 이완 및 마인드맵 파편화) — 참고 지표
        loose_assoc = _clamp01(float(behavioral_metrics.get("loose_association_score", 0.0) or 0.0))
        ego_loss = _clamp01(float(behavioral_metrics.get("ego_boundary_loss_score", 0.0) or 0.0))

        sch_spectrum = {
            "loose_association": round(loose_assoc * 100, 1),
            "thought_blocking": round(min(hesitation_idx * 1.5, 1.0) * 100, 1),
            "ego_boundary_loss": round(ego_loss * 100, 1),
            "delusional_affinity": round(max(loose_assoc, ego_loss) * 90, 1),
        }
        sch_total_avg = (loose_assoc + ego_loss) / 2.0

        # 6) 내재화 총합 지수: 선형 결합 + 상호작용 공병 시너지
        linear_sum = (d_dep * 0.3) + (d_anx_eff * 0.25) + (d_ocd * 0.25) + (d_pan * 0.2)
        interaction_term = (
            self.beta_depression_anxiety * (d_dep * d_anx_eff)
            + self.beta_ocd_panic * (d_ocd * d_pan)
        )
        total_internalizing = min((linear_sum + interaction_term * 0.4) * 100, 100.0)

        # 7) 내재화 참고 경고 레벨
        if total_internalizing >= 80.0:
            risk_level = "HIGH_ALERT"
        elif total_internalizing >= 50.0:
            risk_level = "MONITOR"
        else:
            risk_level = "NORMAL"

        # 8) 지지형 안전 기지 접근으로 강제 스위칭
        suggested_agent = (
            "SUNG_AH_SUPPORT"
            if (sch_total_avg > 0.6 or risk_level == "HIGH_ALERT")
            else "PROST_CONFRONTATION"
        )

        # 9) 디멘전(기존 contract) 산출: total_internalizing이 먼저 계산되었음
        depressive_index = float(d_dep * 100.0)
        anxiety_index = float(d_anx_eff * 100.0)
        obsessive_compulsive = float(d_ocd * 100.0)
        panic_index = float(d_pan * 100.0)
        bipolar_fluctuation_index = float(d_bip * 100.0)
        somatic_symptom_index = float(d_som * 100.0)

        downstream_triggers: Dict[str, Any] = {
            "depression_panic_track_risk": None,
            "ocd_asd_loop": None,
        }

        # 10) 체인드 다운스트림 트리거 #1:
        #    internalizing > 70 → 우울/공황 트랙 리스크를 명시적으로 'ELEVATED' + 차원 보정
        if total_internalizing > 70.0:
            excess = (total_internalizing - 70.0) / 30.0  # 0..1
            excess = min(1.0, max(0.0, excess))
            depression_bump = round(excess * 15.0, 1)
            panic_bump = round(excess * 15.0, 1)

            depressive_index = min(100.0, depressive_index + depression_bump)
            panic_index = min(100.0, panic_index + panic_bump)

            downstream_triggers["depression_panic_track_risk"] = {
                "level": "ELEVATED",
                "trigger_internalizing_threshold": 70.0,
                "depression_bump": depression_bump,
                "panic_bump": panic_bump,
            }
        else:
            downstream_triggers["depression_panic_track_risk"] = {
                "level": "NORMAL",
                "trigger_internalizing_threshold": 70.0,
                "depression_bump": 0.0,
                "panic_bump": 0.0,
            }

        # 11) 체인드 다운스트림 트리거 #2:
        #    internalizing이 높고(>70) 인지 경직(cognitive_rigidity)이 동반되면
        #    OCD/ASD 루프 이슈를 debug-console style 구조로 명시.
        cognitive_rigidity_score = obsessive_compulsive  # 0..100 (obsessive_compulsive dim proxy)
        if total_internalizing > 70.0 and cognitive_rigidity_score >= 60.0:
            downstream_triggers["ocd_asd_loop"] = {
                "enabled": True,
                "issues": [
                    {
                        "code": "OCD_ASD_LOOP",
                        "labelKo": "강박·공황-고착 루프",
                        "severity": "HIGH",
                        "evidence": {
                            "total_internalizing_score": round(total_internalizing, 1),
                            "cognitive_rigidity_score": round(cognitive_rigidity_score, 1),
                            "gs_slowdown_proxy": round(gs_slowdown_proxy, 3),
                            "stimming_proxy": round(stimming_proxy, 3),
                            "defensive_language_signal": round(defensive_language_signal, 3),
                            "panic_index": round(panic_index, 1),
                            "obsessive_compulsive_index": round(obsessive_compulsive, 1),
                        },
                    }
                ],
            }
        else:
            downstream_triggers["ocd_asd_loop"] = {
                "enabled": False,
                "issues": [],
            }

        core_inputs = {
            "gs_slowdown_proxy": round(gs_slowdown_proxy, 3),
            "stimming_proxy": round(stimming_proxy, 3),
            "defensive_language_signal": round(defensive_language_signal, 3),
            # raw-ish supporting fields for debugging
            "word_delay_ms": round(delay_ms, 1),
            "backspace_count": backspace_cnt,
            "word_card_cancel_count": word_card_cancel_count,
        }

        return {
            "total_internalizing_score": round(total_internalizing, 1),
            "internalizing_risk_level": risk_level,
            "suggested_approach": suggested_agent,
            "core_inputs": core_inputs,
            "downstream_triggers": downstream_triggers,
            "internalizing_core": {
                "total_internalizing_score": round(total_internalizing, 1),
                "internalizing_risk_level": risk_level,
                "core_inputs": core_inputs,
                "downstream_triggers": downstream_triggers,
            },
            "dimensions": {
                "depressive_index": round(depressive_index, 1),
                "anxiety_index": round(anxiety_index, 1),
                "obsessive_compulsive": round(obsessive_compulsive, 1),
                "panic_index": round(panic_index, 1),
                "bipolar_fluctuation_index": round(bipolar_fluctuation_index, 1),
                "somatic_symptom_index": round(somatic_symptom_index, 1),
                "schizophrenia_spectrum": sch_spectrum,
            },
            "non_diagnostic": True,
        }


_ENGINE = InternalizingCoreEngine()

# Backwards compatibility (older imports / tests)
UnifiedEmotionalSpectrumEngine = InternalizingCoreEngine

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
    defense_enabled = bool((sanitized or {}).get("defenseMechanismEnabled", True))
    persona = (getattr(state, "persona_routing", None) or {}) if state is not None else {}
    mood_state = str(persona.get("mood_state") or "")
    reason = str(persona.get("reason") or "")
    defensive_language_signal = 0.0
    if defense_enabled and (reason == "defensive_pattern_signal" or mood_state.upper() == "DEFENSIVE"):
        defensive_language_signal = 0.85

    result = _ENGINE.calculate_internalizing_spectrum(
        scores,
        metrics,
        defensive_language_signal=defensive_language_signal,
    )
    result["baseScores"] = {k: round(float(v), 1) for k, v in scores.items()}
    result["behavioralMetrics"] = metrics
    result["approachLabelKo"] = APPROACH_LABELS_KO.get(result["suggested_approach"], "")
    result["mind_room"] = parse_clinical_state_to_room(result)
    result["neurodevelopmental_matrix"] = to_neurodevelopmental_matrix(result)
    return result


def parse_clinical_state_to_room(result: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """스펙트럼 상태 → '마음의 방' 레이아웃 파라미터 (프론트 시각화 계약).

    - 와해성 신호 폭발: 방 레이아웃 파편화 왜곡 + 지지형 페르소나 강제 스위칭
    - 내재화 고위험(강박성 우울·억압): 차갑고 딱딱한 대칭의 고립된 방
    - MONITOR 관찰 구간: 차가운 흰 방 (감정 온도 낮음, 정렬 유지)
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

    if total >= 50.0:
        return {
            "color_tone": "cold-white",
            "lighting_level": 55,
            "wall_symmetry": "rigid",
            "agent_persona": str(doc.get("suggested_approach") or "PROST_CONFRONTATION"),
        }

    return {
        "color_tone": "warm-yellow",
        "lighting_level": 85,
        "wall_symmetry": "natural",
        "agent_persona": "SUNG_AH_SUPPORT",
    }


def to_dsm5_integrated_diagnostic(
    result: Optional[Mapping[str, Any]],
    *,
    session_id: str = "",
    user_id: str = "",
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """엔진 결과 → DSM5IntegratedDiagnostic TS 인터페이스 계약 직렬화.

    프론트(듀얼 에이전트 스위칭 + 가상 방 인테리어 바인딩)가 그대로 소비한다.
    """
    from datetime import datetime, timezone

    doc = dict(result or {})
    room = parse_clinical_state_to_room(doc)
    dims = dict(doc.get("dimensions") or {})
    sch = dict(dims.get("schizophrenia_spectrum") or {})
    return {
        "session_id": session_id or "",
        "user_id": user_id or "",
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "total_internalizing_score": float(doc.get("total_internalizing_score") or 0.0),
        "internalizing_risk_level": str(doc.get("internalizing_risk_level") or "NORMAL"),
        "downstream_triggers": doc.get("downstream_triggers") or None,
        "dimensions": {
            "depressive_index": float(dims.get("depressive_index") or 0.0),
            "anxiety_index": float(dims.get("anxiety_index") or 0.0),
            "obsessive_compulsive": float(dims.get("obsessive_compulsive") or 0.0),
            "panic_index": float(dims.get("panic_index") or 0.0),
            "bipolar_fluctuation_index": float(dims.get("bipolar_fluctuation_index") or 0.0),
            "somatic_symptom_index": float(dims.get("somatic_symptom_index") or 0.0),
            "schizophrenia_spectrum": {
                "loose_association": float(sch.get("loose_association") or 0.0),
                "thought_blocking": float(sch.get("thought_blocking") or 0.0),
                "ego_boundary_loss": float(sch.get("ego_boundary_loss") or 0.0),
                "delusional_affinity": float(sch.get("delusional_affinity") or 0.0),
            },
        },
        "clinical_meta": {
            "suggested_approach": str(doc.get("suggested_approach") or "PROST_CONFRONTATION"),
            "room_projection": {
                "color_tone": room["color_tone"],
                "lighting_level": int(room["lighting_level"]),
                "wall_symmetry": room["wall_symmetry"],
            },
        },
        "non_diagnostic": True,
    }


def to_integrated_diagnostic_model(
    result: Optional[Mapping[str, Any]],
    *,
    session_id: str = "",
    patient_id: str = "",
) -> Dict[str, Any]:
    """
    엔진 결과 → IntegratedDiagnosticModel TS 인터페이스 계약 직렬화.

    - 인지 프로필(CognitiveProfile)은 체크인 기반의 비진단 참고 지표로 매핑
    - 임상 프로필(clinicalProfile)도 비진단 참고 지표로만 제공
    - threeRenderMetrics는 3D 렌더러 노드 스케일 힌트로 사용
    """
    doc = dict(result or {})
    base_scores = dict(doc.get("baseScores") or {})
    dims = dict(doc.get("dimensions") or {})

    # cognitiveProfile proxy: 체크인 가중치 보정값(우울/불안/신체화 프록시)으로 "그릇 크기"를 안정적으로 추정
    d_dep = float(base_scores.get("depressive", 50) or 50)
    d_anx = float(base_scores.get("anxiety", 50) or 50)
    d_som = float(base_scores.get("somatic", 50) or 50)

    # 안정성(0-100): 우울/불안/신체화가 낮을수록 인지 안정이 높아지는 방향
    stability = (100.0 - d_dep) * 0.35 + (100.0 - d_anx) * 0.35 + (100.0 - d_som) * 0.30
    stability = max(0.0, min(100.0, stability))

    def _clamp150(x: float) -> float:
        return max(0.0, min(150.0, float(x)))

    g_factor = _clamp150(50.0 + stability)  # 50..150
    crystallized_gc = _clamp150(45.0 + (100.0 - d_dep) * 0.55 + (100.0 - d_anx) * 0.15)
    fluid_gf = _clamp150(40.0 + (100.0 - d_anx) * 0.40 + (100.0 - d_som) * 0.40)
    working_memory_gwm = _clamp150(35.0 + (100.0 - d_anx) * 0.50 + (100.0 - d_dep) * 0.20)
    processing_speed_gs = _clamp150(30.0 + (100.0 - d_som) * 0.55 + (100.0 - d_anx) * 0.15)
    visual_processing_gv = _clamp150(30.0 + (100.0 - d_dep) * 0.35 + (100.0 - d_som) * 0.45)

    # clinicalProfile: dimensions 기반 비진단 참고 지표
    schizophrenia_dim = dict(dims.get("schizophrenia_spectrum") or {})
    loose_assoc = float(schizophrenia_dim.get("loose_association", 0.0) or 0.0)
    ego_boundary_loss = float(schizophrenia_dim.get("ego_boundary_loss", 0.0) or 0.0)
    schizophrenia_index = max(0.0, min(100.0, (loose_assoc + ego_boundary_loss) / 2.0))

    depression_index = max(0.0, min(100.0, float(dims.get("depressive_index", 0.0) or 0.0)))
    obsessive_compulsive = max(
        0.0, min(100.0, float(dims.get("obsessive_compulsive", 0.0) or 0.0))
    )
    panic_index = max(0.0, min(100.0, float(dims.get("panic_index", 0.0) or 0.0)))

    # ASD stimming proxy: 강박적 고정/통제(OC) + 공황 각성(PI)로 "자극·반복성" 참고 지표 구성
    asd_stimming_index = max(
        0.0,
        min(100.0, obsessive_compulsive * 0.6 + panic_index * 0.4),
    )

    # threeRenderMetrics: 3D 렌더러 노드 스케일 힌트
    # backbone_tension이 낮을수록 "인지 와해" 경향(안정성 저하, sch 신호 증가)
    backbone_tension = max(
        0.0,
        min(
            100.0,
            (g_factor / 150.0) * 100.0 * (1.0 - schizophrenia_index / 200.0),
        ),
    )

    cluster_density = max(
        0.0,
        min(100.0, asd_stimming_index * 0.7 + schizophrenia_index * 0.3),
    )

    # Core internalizing pressure: 핵심 점수가 높을수록 '인지 안정(Backbone)'을 약화시키는 시각적 반영.
    internalizing_total = float(doc.get("total_internalizing_score") or 0.0)
    pressure = min(1.0, max(0.0, internalizing_total / 100.0))
    backbone_tension = max(0.0, min(100.0, backbone_tension * (1.0 - 0.18 * pressure)))
    cluster_density = max(0.0, min(100.0, cluster_density * (1.0 + 0.10 * pressure)))

    return {
        "sessionId": session_id or "",
        "patientId": patient_id or "",
        "internalizing_core": {
            "total_internalizing_score": round(internalizing_total, 1),
            "internalizing_risk_level": str(doc.get("internalizing_risk_level") or "NORMAL"),
            "downstream_triggers": doc.get("downstream_triggers") or None,
        },
        "cognitiveProfile": {
            "g_factor": round(g_factor, 1),
            "crystallized_gc": round(crystallized_gc, 1),
            "fluid_gf": round(fluid_gf, 1),
            "working_memory_gwm": round(working_memory_gwm, 1),
            "processing_speed_gs": round(processing_speed_gs, 1),
            "visual_processing_gv": round(visual_processing_gv, 1),
        },
        "clinicalProfile": {
            "schizophrenia_index": round(schizophrenia_index, 1),
            "asd_stimming_index": round(asd_stimming_index, 1),
            "depression_index": round(depression_index, 1),
        },
        "threeRenderMetrics": {
            "backbone_tension": round(backbone_tension, 1),
            "cluster_density": round(cluster_density, 1),
        },
    }


def to_neurodevelopmental_matrix(
    result: Optional[Mapping[str, Any]],
    *,
    session_id: str = "",
    word_card_analysis: Optional[Mapping[str, Any]] = None,
    mindmap: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """엔진 결과 → NeurodevelopmentalCognitiveMatrix TS 계약 직렬화 (비진단 웰니스 참고 지표)."""
    doc = dict(result or {})
    dims = doc.get("dimensions") or {}
    sch = dims.get("schizophrenia_spectrum") or {}
    behavioral = doc.get("behavioralMetrics") or {}

    hesitation = float(behavioral.get("hesitation_index", 0.0) or 0.0)
    sch_avg = (
        float(sch.get("loose_association", 0.0) or 0.0)
        + float(sch.get("ego_boundary_loss", 0.0) or 0.0)
    ) / 200.0  # normalized 0-1

    wc = dict(word_card_analysis or {})
    boundary_score = float(wc.get("boundaryScore", 0.5) or 0.5)
    mindmap_boundary = float((mindmap or {}).get("boundaryScore", boundary_score) or boundary_score)

    # cognitive_disorganization_score: 기존(와해/불안/경계) 기반 + internalizing_core 압력 블렌딩
    cds_base = min(
        100.0,
        max(
            0.0,
            (sch_avg * 50.0 + hesitation * 30.0 + (1.0 - boundary_score) * 20.0) * 2.0,
        ),
    )
    total_internalizing = float(doc.get("total_internalizing_score") or 0.0)
    cds = min(100.0, max(0.0, cds_base * 0.7 + total_internalizing * 0.3))

    # spectrum_mapping
    social_blindness = min(100.0, max(0.0, (1.0 - boundary_score) * 100.0))
    rigid_fixation = min(100.0, max(0.0, float(dims.get("obsessive_compulsive", 0.0) or 0.0)))

    ego_loss = float(sch.get("ego_boundary_loss", 0.0) or 0.0)
    cognitive_fragmentation = min(100.0, max(0.0, (ego_loss + (1.0 - mindmap_boundary) * 100.0) / 2.0))

    loose = float(sch.get("loose_association", 0.0) or 0.0)
    delusional = float(sch.get("delusional_affinity", 0.0) or 0.0)
    reality_detachment = min(100.0, max(0.0, (loose + delusional) / 2.0))

    # three_d_room_fx
    if rigid_fixation > 60 and social_blindness > 60:
        wall_texture = "isolated-island"
    elif cognitive_fragmentation > 60 or reality_detachment > 60:
        wall_texture = "wireframe-dissolve"
    else:
        wall_texture = "rigid-grid"

    sound_muffling_factor = min(1.0, (social_blindness + rigid_fixation) / 200.0)

    return {
        "cognitive_disorganization_score": round(cds, 1),
        "spectrum_mapping": {
            "social_blindness": round(social_blindness, 1),
            "rigid_fixation": round(rigid_fixation, 1),
            "cognitive_fragmentation": round(cognitive_fragmentation, 1),
            "reality_detachment": round(reality_detachment, 1),
        },
        "three_d_room_fx": {
            "wall_texture": wall_texture,
            "sound_muffling_factor": round(sound_muffling_factor, 4),
        },
        "non_diagnostic": True,
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
