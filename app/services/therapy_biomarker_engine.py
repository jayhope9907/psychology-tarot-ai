"""Therapy biomarker engine — full ClinicalSchool axis coverage.

TS 계약: ``static/types/TherapyBiomarkerEngine.ts``

원본 9축(정신분석~긍정심리) + ClinicalSchool 전 학파의 행동 프록시 점수를
0~100으로 환산한다. 비진단(non_diagnostic).
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

from app.models.clinical import ClinicalSchool

# kind: latency | duration | ratio | error | boost
# score formulas (TS parity):
#   latency: clamp(100 - v * coef)
#   duration: clamp(v * coef)
#   ratio:   clamp(v * 100)          # v expected 0..1
#   error:   clamp(100 - abs(v)*coef)
#   boost:   clamp(v * coef)

AXIS_SPECS: List[Dict[str, Any]] = [
    # —— Classic 9 ——
    {"id": "insightScore", "school": "FREUDIAN", "raw": "psychoanalysisInsightMs", "kind": "latency", "coef": 0.05, "label_ko": "정신분석 · 통찰", "wave": "classic"},
    {"id": "courageScore", "school": "ADLERIAN", "raw": "adlerResilienceDelayMs", "kind": "latency", "coef": 0.08, "label_ko": "아들러 · 용기", "wave": "classic"},
    {"id": "meaningScore", "school": "LOGOTHERAPY", "raw": "logotherapyEnduranceSec", "kind": "duration", "coef": 5.0, "label_ko": "의미치료 · 견딤", "wave": "classic"},
    {"id": "acceptanceScore", "school": "ROGERIAN", "raw": "personCenteredStability", "kind": "error", "coef": 10.0, "label_ko": "인간중심 · 자기수용", "wave": "classic"},
    {"id": "autonomyScore", "school": "EXISTENTIAL", "raw": "existentialAutonomyRatio", "kind": "ratio", "coef": 1.0, "label_ko": "실존주의 · 자율", "wave": "classic"},
    {"id": "realityScore", "school": "REALITY_THERAPY", "raw": "realityFocusRatio", "kind": "ratio", "coef": 1.0, "label_ko": "현실치료 · 초점", "wave": "classic"},
    {"id": "cbtShiftScore", "school": "BECK_CBT", "raw": "cbtCognitiveShiftMs", "kind": "latency", "coef": 0.04, "label_ko": "CBT · 인지전환", "wave": "classic"},
    {"id": "solutionScore", "school": "SOLUTION_FOCUSED", "raw": "solutionOrientedRatio", "kind": "ratio", "coef": 1.0, "label_ko": "해결중심 · 해결집중", "wave": "classic"},
    {"id": "strengthsScore", "school": "POSITIVE_PSYCHOLOGY", "raw": "positiveStrengthBoost", "kind": "boost", "coef": 10.0, "label_ko": "긍정심리 · 강점", "wave": "classic"},
    # —— Humanistic / existential extras ——
    {"id": "gestaltPresenceScore", "school": "GESTALT", "raw": "gestaltHereNowRatio", "kind": "ratio", "coef": 1.0, "label_ko": "게슈탈트 · 지금여기", "wave": "humanistic"},
    # —— Modern CBT family ——
    {"id": "rebtDisputeScore", "school": "REBT", "raw": "rebtDisputeSuccessRatio", "kind": "ratio", "coef": 1.0, "label_ko": "REBT · 논박", "wave": "modern_cbt"},
    {"id": "dbtRegulationScore", "school": "DBT", "raw": "dbtDistressToleranceRatio", "kind": "ratio", "coef": 1.0, "label_ko": "DBT · 고통감내", "wave": "modern_cbt"},
    {"id": "actValuesScore", "school": "ACT", "raw": "actValuesCommittedActionRatio", "kind": "ratio", "coef": 1.0, "label_ko": "ACT · 가치전념", "wave": "modern_cbt"},
    {"id": "schemaModeShiftScore", "school": "SCHEMA_THERAPY", "raw": "schemaModeShiftMs", "kind": "latency", "coef": 0.045, "label_ko": "스키마 · 모드전환", "wave": "modern_cbt"},
    {"id": "mbctDecenteringScore", "school": "MBCT", "raw": "mbctDecenteringRatio", "kind": "ratio", "coef": 1.0, "label_ko": "MBCT · 탈중심", "wave": "modern_cbt"},
    {"id": "cftCompassionScore", "school": "CFT", "raw": "cftSelfCompassionRatio", "kind": "ratio", "coef": 1.0, "label_ko": "CFT · 자기자비", "wave": "modern_cbt"},
    {"id": "baActivationScore", "school": "BEHAVIORAL_ACTIVATION", "raw": "baActivityCompletionRatio", "kind": "ratio", "coef": 1.0, "label_ko": "BA · 행동활성화", "wave": "modern_cbt"},
    # —— Psychodynamic+ ——
    {"id": "jungianSymbolScore", "school": "JUNGIAN", "raw": "jungianSymbolAssociationRatio", "kind": "ratio", "coef": 1.0, "label_ko": "융 · 상징연결", "wave": "psychodynamic"},
    {"id": "objectRelationsScore", "school": "OBJECT_RELATIONS", "raw": "objectRelationsStabilityRatio", "kind": "ratio", "coef": 1.0, "label_ko": "대상관계 · 내적대상", "wave": "psychodynamic"},
    {"id": "selfPsychologyScore", "school": "SELF_PSYCHOLOGY", "raw": "selfPsychologyMirroringRatio", "kind": "ratio", "coef": 1.0, "label_ko": "자기심리학 · 미러링", "wave": "psychodynamic"},
    {"id": "taScriptScore", "school": "TRANSACTIONAL_ANALYSIS", "raw": "taAdultEgoRatio", "kind": "ratio", "coef": 1.0, "label_ko": "TA · 성인자아", "wave": "psychodynamic"},
    # —— Systemic / relational ——
    {"id": "narrativeExternalizeScore", "school": "NARRATIVE", "raw": "narrativeExternalizationRatio", "kind": "ratio", "coef": 1.0, "label_ko": "서사치료 · 외재화", "wave": "systemic"},
    {"id": "iptRoleScore", "school": "IPT", "raw": "iptInterpersonalRepairRatio", "kind": "ratio", "coef": 1.0, "label_ko": "IPT · 관계회복", "wave": "systemic"},
    {"id": "bowenDifferentiationScore", "school": "BOWEN_SYSTEMS", "raw": "bowenDifferentiationRatio", "kind": "ratio", "coef": 1.0, "label_ko": "보웬 · 분화", "wave": "systemic"},
    {"id": "structuralBoundaryScore", "school": "STRUCTURAL_FAMILY", "raw": "structuralBoundaryClarityRatio", "kind": "ratio", "coef": 1.0, "label_ko": "구조가족 · 경계", "wave": "systemic"},
    {"id": "satirCongruenceScore", "school": "SATIR", "raw": "satirCongruenceRatio", "kind": "ratio", "coef": 1.0, "label_ko": "사티어 · 일치소통", "wave": "systemic"},
    {"id": "strategicReframeScore", "school": "STRATEGIC_FAMILY", "raw": "strategicReframeSuccessRatio", "kind": "ratio", "coef": 1.0, "label_ko": "전략가족 · 재구성", "wave": "systemic"},
    {"id": "attachmentSecureScore", "school": "ATTACHMENT", "raw": "attachmentSecureBaseRatio", "kind": "ratio", "coef": 1.0, "label_ko": "애착 · 안전기지", "wave": "systemic"},
    {"id": "eftBondScore", "school": "EFT", "raw": "eftEmotionalBondRatio", "kind": "ratio", "coef": 1.0, "label_ko": "EFT · 정서유대", "wave": "systemic"},
    # —— Brief / trauma / emotion ——
    {"id": "miChangeTalkScore", "school": "MOTIVATIONAL", "raw": "miChangeTalkRatio", "kind": "ratio", "coef": 1.0, "label_ko": "MI · 변화대화", "wave": "brief_trauma"},
    {"id": "traumaSafetyScore", "school": "TRAUMA_INFORMED", "raw": "traumaSafetyCueRatio", "kind": "ratio", "coef": 1.0, "label_ko": "트라우마정보 · 안전", "wave": "brief_trauma"},
    {"id": "emdrStabilizeScore", "school": "EMDR_INFORMED", "raw": "emdrStabilizationRatio", "kind": "ratio", "coef": 1.0, "label_ko": "EMDR안내 · 안정화", "wave": "brief_trauma"},
    {"id": "ifsSelfLeadershipScore", "school": "IFS", "raw": "ifsSelfLeadershipRatio", "kind": "ratio", "coef": 1.0, "label_ko": "IFS · Self리더십", "wave": "brief_trauma"},
    {"id": "cptStuckPointScore", "school": "CPT_INFORMED", "raw": "cptStuckPointShiftMs", "kind": "latency", "coef": 0.04, "label_ko": "CPT안내 · stuck point", "wave": "brief_trauma"},
    {"id": "seTitrationScore", "school": "SOMATIC_EXPERIENCING", "raw": "seTitrationSafetyRatio", "kind": "ratio", "coef": 1.0, "label_ko": "SE안내 · 타이틀레이션", "wave": "brief_trauma"},
    {"id": "peApproachScore", "school": "PROLONGED_EXPOSURE_INFORMED", "raw": "peGradualApproachRatio", "kind": "ratio", "coef": 1.0, "label_ko": "PE안내 · 점진접근", "wave": "brief_trauma"},
    # —— Expressive ——
    {"id": "psychodramaRoleScore", "school": "PSYCHODRAMA", "raw": "psychodramaRoleFlexibilityRatio", "kind": "ratio", "coef": 1.0, "label_ko": "심리극 · 역할유연", "wave": "expressive"},
    {"id": "dramaTherapyScore", "school": "DRAMA_THERAPY", "raw": "dramaTherapyExpressionRatio", "kind": "ratio", "coef": 1.0, "label_ko": "연극치료 · 표현", "wave": "expressive"},
    {"id": "artTherapyScore", "school": "ART_THERAPY", "raw": "artTherapySymbolFluencyRatio", "kind": "ratio", "coef": 1.0, "label_ko": "미술치료 · 상징유창", "wave": "expressive"},
    {"id": "musicTherapyScore", "school": "MUSIC_THERAPY", "raw": "musicTherapyAttunementRatio", "kind": "ratio", "coef": 1.0, "label_ko": "음악치료 · 조율", "wave": "expressive"},
    {"id": "danceMovementScore", "school": "DANCE_MOVEMENT", "raw": "danceMovementEmbodimentRatio", "kind": "ratio", "coef": 1.0, "label_ko": "무용치료 · 체화", "wave": "expressive"},
    {"id": "playTherapyScore", "school": "PLAY_THERAPY", "raw": "playTherapySpontaneityRatio", "kind": "ratio", "coef": 1.0, "label_ko": "놀이치료 · 자발성", "wave": "expressive"},
    {"id": "sandplayScore", "school": "SANDPLAY", "raw": "sandplaySceneCoherenceRatio", "kind": "ratio", "coef": 1.0, "label_ko": "모래놀이 · 장면응집", "wave": "expressive"},
    # —— Integrative / contextual ——
    {"id": "mindfulnessScore", "school": "MINDFULNESS", "raw": "mindfulnessPresentMomentRatio", "kind": "ratio", "coef": 1.0, "label_ko": "마음챙김 · 현재", "wave": "integrative"},
    {"id": "feministEmpowerScore", "school": "FEMINIST", "raw": "feministEmpowermentRatio", "kind": "ratio", "coef": 1.0, "label_ko": "페미니스트 · 임파워", "wave": "integrative"},
    {"id": "multiculturalHumilityScore", "school": "MULTICULTURAL", "raw": "multiculturalHumilityRatio", "kind": "ratio", "coef": 1.0, "label_ko": "다문화 · 겸손", "wave": "integrative"},
    {"id": "polyvagalSafetyScore", "school": "POLYVAGAL_INFORMED", "raw": "polyvagalSafetySignalRatio", "kind": "ratio", "coef": 1.0, "label_ko": "다미주 · 안전신호", "wave": "integrative"},
    {"id": "integrativeFitScore", "school": "INTEGRATIVE", "raw": "integrativeTechniqueFitRatio", "kind": "ratio", "coef": 1.0, "label_ko": "통합 · 맞춤적합", "wave": "integrative"},
    # —— Addiction / recovery (wellness proxies) ——
    {"id": "relapsePreventionScore", "school": "RELAPSE_PREVENTION", "raw": "relapseHighRiskCopingRatio", "kind": "ratio", "coef": 1.0, "label_ko": "재발예방 · 고위험대처", "wave": "addiction"},
    {"id": "contingencyScore", "school": "CONTINGENCY_MANAGEMENT", "raw": "contingencyRewardFollowThroughRatio", "kind": "ratio", "coef": 1.0, "label_ko": "유관관리 · 보상이행", "wave": "addiction"},
    {"id": "craScore", "school": "CRA_COMMUNITY", "raw": "craCommunitySupportRatio", "kind": "ratio", "coef": 1.0, "label_ko": "CRA · 지역지원", "wave": "addiction"},
    {"id": "craftScore", "school": "CRAFT_FAMILY", "raw": "craftFamilyInviteRatio", "kind": "ratio", "coef": 1.0, "label_ko": "CRAFT · 가족초대", "wave": "addiction"},
    {"id": "twelveStepScore", "school": "TWELVE_STEP_FACILITATION", "raw": "twelveStepMeetingEngagementRatio", "kind": "ratio", "coef": 1.0, "label_ko": "12단계 · 모임참여", "wave": "addiction"},
    {"id": "matrixScore", "school": "MATRIX_MODEL", "raw": "matrixStructureAdherenceRatio", "kind": "ratio", "coef": 1.0, "label_ko": "매트릭스 · 구조이행", "wave": "addiction"},
    {"id": "harmReductionScore", "school": "HARM_REDUCTION", "raw": "harmReductionSafetyPlanRatio", "kind": "ratio", "coef": 1.0, "label_ko": "위해감축 · 안전계획", "wave": "addiction"},
    {"id": "smartRecoveryScore", "school": "SMART_RECOVERY", "raw": "smartRecoveryToolUseRatio", "kind": "ratio", "coef": 1.0, "label_ko": "SMART · 도구사용", "wave": "addiction"},
    {"id": "addictionCbtScore", "school": "ADDICTION_CBT", "raw": "addictionCbtUrgeSurfMs", "kind": "latency", "coef": 0.05, "label_ko": "중독CBT · 욕구서핑", "wave": "addiction"},
    {"id": "cravingMindfulnessScore", "school": "CRAVING_MINDFULNESS", "raw": "cravingMindfulnessObserveRatio", "kind": "ratio", "coef": 1.0, "label_ko": "갈망챙김 · 관찰", "wave": "addiction"},
]

_DEFAULTS: Dict[str, float] = {
    "psychoanalysisInsightMs": 800.0,
    "adlerResilienceDelayMs": 600.0,
    "logotherapyEnduranceSec": 8.0,
    "personCenteredStability": 2.0,
    "existentialAutonomyRatio": 0.5,
    "realityFocusRatio": 0.5,
    "cbtCognitiveShiftMs": 700.0,
    "solutionOrientedRatio": 0.5,
    "positiveStrengthBoost": 5.0,
}


def _num(raw: Mapping[str, Any], key: str, default: float = 0.5) -> float:
    try:
        value = raw.get(key, default)
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _clamp(n: float) -> float:
    if n != n:
        return 0.0
    return max(0.0, min(100.0, n))


def _round1(n: float) -> float:
    return round(n * 10.0) / 10.0


def _score_axis(kind: str, value: float, coef: float) -> float:
    if kind == "latency":
        return _clamp(100.0 - value * coef)
    if kind == "duration":
        return _clamp(value * coef)
    if kind == "ratio":
        return _clamp(value * 100.0)
    if kind == "error":
        return _clamp(100.0 - abs(value) * coef)
    if kind == "boost":
        return _clamp(value * coef)
    return 50.0


def get_therapy_catalog() -> Dict[str, Any]:
    from app.services.therapy_evidence_corpus import (
        attach_evidence_to_axes,
        build_evidence_corpus,
    )

    waves: Dict[str, int] = {}
    for spec in AXIS_SPECS:
        waves[spec["wave"]] = waves.get(spec["wave"], 0) + 1
    axes = [
        {
            "id": s["id"],
            "theory": s["school"].lower(),
            "school": s["school"],
            "raw": s["raw"],
            "kind": s["kind"],
            "label_ko": s["label_ko"],
            "wave": s["wave"],
        }
        for s in AXIS_SPECS
    ]
    evidence = build_evidence_corpus()
    return {
        "axes": attach_evidence_to_axes(axes),
        "count": len(AXIS_SPECS),
        "waves": waves,
        "clinical_school_count": len(ClinicalSchool),
        "evidence_paper_count": evidence["paper_count"],
        "evidence_disclaimer": evidence["disclaimer"],
        "architecture_hooks": [
            "process_based_therapy",
            "fit_session_feedback",
            "trauma_safety_gate",
            "aai_attachment_coherence",
            "pesm_ecological_systems",
            "therapy_evidence_corpus",
        ],
        "non_diagnostic": True,
        "ts_contract": "/static/types/TherapyBiomarkerEngine.ts",
    }


class TherapyEngineCalculator:
    """Full-school raw → 0~100 vector + 2인 Quant Complementary Alpha."""

    def extract_therapy_vector(self, user_id: str, raw: Mapping[str, Any]) -> Dict[str, Any]:
        scores: Dict[str, Any] = {"userId": user_id, "non_diagnostic": True}
        by_school: Dict[str, float] = {}
        for spec in AXIS_SPECS:
            default = _DEFAULTS.get(spec["raw"], 0.5 if spec["kind"] == "ratio" else 500.0)
            if spec["kind"] == "duration":
                default = _DEFAULTS.get(spec["raw"], 8.0)
            if spec["kind"] == "error":
                default = _DEFAULTS.get(spec["raw"], 2.0)
            if spec["kind"] == "boost":
                default = _DEFAULTS.get(spec["raw"], 5.0)
            if spec["kind"] == "latency":
                default = _DEFAULTS.get(spec["raw"], 600.0)
            value = _num(raw, spec["raw"], default)
            score = _round1(_score_axis(spec["kind"], value, float(spec["coef"])))
            # solutionScore stays int in classic contract
            if spec["id"] == "solutionScore":
                score = int(round(score))
            scores[spec["id"]] = score
            by_school[spec["school"]] = float(score)
        scores["bySchool"] = by_school
        scores["axisCount"] = len(AXIS_SPECS)
        return scores

    def top_schools(self, vector: Mapping[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        by_school = vector.get("bySchool") or {}
        ranked = sorted(by_school.items(), key=lambda kv: kv[1], reverse=True)
        out = []
        for school, score in ranked[: max(1, limit)]:
            spec = next((s for s in AXIS_SPECS if s["school"] == school), None)
            out.append(
                {
                    "school": school,
                    "score": score,
                    "label_ko": (spec or {}).get("label_ko", school),
                    "wave": (spec or {}).get("wave", ""),
                }
            )
        return out

    def calculate_therapeutic_synergy(
        self,
        user_a: Mapping[str, Any],
        user_b: Mapping[str, Any],
    ) -> Dict[str, Any]:
        a_cbt = _num(user_a, "cbtShiftScore", 50.0)
        b_cbt = _num(user_b, "cbtShiftScore", 50.0)
        a_sol = _num(user_a, "solutionScore", 50.0)
        b_sol = _num(user_b, "solutionScore", 50.0)
        a_courage = _num(user_a, "courageScore", 50.0)
        b_courage = _num(user_b, "courageScore", 50.0)

        # modern layer: DBT × ACT × trauma safety
        a_dbt = _num(user_a, "dbtRegulationScore", 50.0)
        b_dbt = _num(user_b, "dbtRegulationScore", 50.0)
        a_act = _num(user_a, "actValuesScore", 50.0)
        b_act = _num(user_b, "actValuesScore", 50.0)
        a_trauma = _num(user_a, "traumaSafetyScore", 50.0)
        b_trauma = _num(user_b, "traumaSafetyScore", 50.0)

        cognitive_harmony = 100.0 - abs(a_cbt - b_cbt)
        solution_synergy = (a_sol + b_sol) / 2.0
        courage_balance = abs(a_courage - b_courage)
        complement_alpha = 100.0 - abs(courage_balance - 30.0)
        modern_harmony = (
            (100.0 - abs(a_dbt - b_dbt)) * 0.34
            + ((a_act + b_act) / 2.0) * 0.33
            + ((a_trauma + b_trauma) / 2.0) * 0.33
        )

        classic = cognitive_harmony * 0.4 + solution_synergy * 0.3 + complement_alpha * 0.3
        final_score = int(round(classic * 0.7 + modern_harmony * 0.3))

        if a_sol > 70:
            primary = "해결중심적 스페셜리스트"
        elif a_act > 70:
            primary = "ACT 가치전념형 파트너"
        elif a_dbt > 70:
            primary = "DBT 감정조절형 파트너"
        else:
            primary = "인지적 유연형 파트너"

        return {
            "finalTherapyMatchScore": final_score,
            "primaryTherapeuticType": primary,
            "recommendedTherapyIcebreaker": (
                f"두 분은 [해결중심 + CBT + 최신(DBT/ACT/트라우마안전)] 상성 알파 {final_score}점입니다. "
                "위기 상황에서 서로의 인지·감정조절·가치를 보완해 주는 조합이에요!"
            ),
            "components": {
                "cognitiveHarmony": _round1(cognitive_harmony),
                "solutionSynergy": _round1(solution_synergy),
                "complementAlpha": _round1(complement_alpha),
                "modernHarmony": _round1(modern_harmony),
            },
            "topSchoolsA": self.top_schools(user_a, 3),
            "topSchoolsB": self.top_schools(user_b, 3),
            "non_diagnostic": True,
        }


def extract_therapy_vector(user_id: str, raw: Mapping[str, Any]) -> Dict[str, Any]:
    return TherapyEngineCalculator().extract_therapy_vector(user_id, raw)


def calculate_therapeutic_synergy(
    user_a: Mapping[str, Any],
    user_b: Mapping[str, Any],
) -> Dict[str, Any]:
    return TherapyEngineCalculator().calculate_therapeutic_synergy(user_a, user_b)


def assert_axes_cover_clinical_schools() -> List[str]:
    covered = {s["school"] for s in AXIS_SPECS}
    missing = [school.value for school in ClinicalSchool if school.value not in covered]
    return missing
