// ============================================================================
// ARCHITECTURE: FULL CLINICAL-SCHOOL THERAPY BIOMARKER ENGINE
// Classic 9 + modern CBT/trauma/systemic/expressive/addiction axes
// (parity with every ClinicalSchool in app/models/clinical.py)
//
// Backend twin:
//   - app/services/therapy_biomarker_engine.py
//   - GET  /api/v1/therapy-biomarkers/catalog
//   - POST /api/v1/therapy-biomarkers/extract
//   - POST /api/v1/therapy-biomarkers/synergy
//
// 비진단 웰니스 참고 지표 (non_diagnostic).
// ============================================================================

export type ScoreKind = "latency" | "duration" | "ratio" | "error" | "boost";

export interface TherapyAxisSpec {
  id: string;
  school: string;
  raw: string;
  kind: ScoreKind;
  coef: number;
  label_ko: string;
  wave: string;
}

/** Classic 9 raw fields (always present) + open modern proxies. */
export interface TherapyBiomarkerRaw {
  psychoanalysisInsightMs?: number;
  adlerResilienceDelayMs?: number;
  logotherapyEnduranceSec?: number;
  personCenteredStability?: number;
  existentialAutonomyRatio?: number;
  realityFocusRatio?: number;
  cbtCognitiveShiftMs?: number;
  solutionOrientedRatio?: number;
  positiveStrengthBoost?: number;
  [rawKey: string]: number | undefined;
}

export interface TherapyProfileVector {
  userId: string;
  insightScore: number;
  courageScore: number;
  meaningScore: number;
  acceptanceScore: number;
  autonomyScore: number;
  realityScore: number;
  cbtShiftScore: number;
  solutionScore: number;
  strengthsScore: number;
  bySchool?: Record<string, number>;
  axisCount?: number;
  non_diagnostic?: true;
  [scoreId: string]: number | string | boolean | Record<string, number> | undefined;
}

export interface TherapeuticSynergyResult {
  finalTherapyMatchScore: number;
  primaryTherapeuticType: string;
  recommendedTherapyIcebreaker: string;
  components: {
    cognitiveHarmony: number;
    solutionSynergy: number;
    complementAlpha: number;
    modernHarmony?: number;
  };
  topSchoolsA?: Array<{ school: string; score: number; label_ko: string; wave: string }>;
  topSchoolsB?: Array<{ school: string; score: number; label_ko: string; wave: string }>;
  non_diagnostic: true;
}

/** Mirrors AXIS_SPECS in therapy_biomarker_engine.py (keep in sync). */
export const THERAPY_AXIS_SPECS: TherapyAxisSpec[] = [
  { id: "insightScore", school: "FREUDIAN", raw: "psychoanalysisInsightMs", kind: "latency", coef: 0.05, label_ko: "정신분석 · 통찰", wave: "classic" },
  { id: "courageScore", school: "ADLERIAN", raw: "adlerResilienceDelayMs", kind: "latency", coef: 0.08, label_ko: "아들러 · 용기", wave: "classic" },
  { id: "meaningScore", school: "LOGOTHERAPY", raw: "logotherapyEnduranceSec", kind: "duration", coef: 5.0, label_ko: "의미치료 · 견딤", wave: "classic" },
  { id: "acceptanceScore", school: "ROGERIAN", raw: "personCenteredStability", kind: "error", coef: 10.0, label_ko: "인간중심 · 자기수용", wave: "classic" },
  { id: "autonomyScore", school: "EXISTENTIAL", raw: "existentialAutonomyRatio", kind: "ratio", coef: 1.0, label_ko: "실존주의 · 자율", wave: "classic" },
  { id: "realityScore", school: "REALITY_THERAPY", raw: "realityFocusRatio", kind: "ratio", coef: 1.0, label_ko: "현실치료 · 초점", wave: "classic" },
  { id: "cbtShiftScore", school: "BECK_CBT", raw: "cbtCognitiveShiftMs", kind: "latency", coef: 0.04, label_ko: "CBT · 인지전환", wave: "classic" },
  { id: "solutionScore", school: "SOLUTION_FOCUSED", raw: "solutionOrientedRatio", kind: "ratio", coef: 1.0, label_ko: "해결중심 · 해결집중", wave: "classic" },
  { id: "strengthsScore", school: "POSITIVE_PSYCHOLOGY", raw: "positiveStrengthBoost", kind: "boost", coef: 10.0, label_ko: "긍정심리 · 강점", wave: "classic" },
  { id: "gestaltPresenceScore", school: "GESTALT", raw: "gestaltHereNowRatio", kind: "ratio", coef: 1.0, label_ko: "게슈탈트 · 지금여기", wave: "humanistic" },
  { id: "rebtDisputeScore", school: "REBT", raw: "rebtDisputeSuccessRatio", kind: "ratio", coef: 1.0, label_ko: "REBT · 논박", wave: "modern_cbt" },
  { id: "dbtRegulationScore", school: "DBT", raw: "dbtDistressToleranceRatio", kind: "ratio", coef: 1.0, label_ko: "DBT · 고통감내", wave: "modern_cbt" },
  { id: "actValuesScore", school: "ACT", raw: "actValuesCommittedActionRatio", kind: "ratio", coef: 1.0, label_ko: "ACT · 가치전념", wave: "modern_cbt" },
  { id: "schemaModeShiftScore", school: "SCHEMA_THERAPY", raw: "schemaModeShiftMs", kind: "latency", coef: 0.045, label_ko: "스키마 · 모드전환", wave: "modern_cbt" },
  { id: "mbctDecenteringScore", school: "MBCT", raw: "mbctDecenteringRatio", kind: "ratio", coef: 1.0, label_ko: "MBCT · 탈중심", wave: "modern_cbt" },
  { id: "cftCompassionScore", school: "CFT", raw: "cftSelfCompassionRatio", kind: "ratio", coef: 1.0, label_ko: "CFT · 자기자비", wave: "modern_cbt" },
  { id: "baActivationScore", school: "BEHAVIORAL_ACTIVATION", raw: "baActivityCompletionRatio", kind: "ratio", coef: 1.0, label_ko: "BA · 행동활성화", wave: "modern_cbt" },
  { id: "jungianSymbolScore", school: "JUNGIAN", raw: "jungianSymbolAssociationRatio", kind: "ratio", coef: 1.0, label_ko: "융 · 상징연결", wave: "psychodynamic" },
  { id: "objectRelationsScore", school: "OBJECT_RELATIONS", raw: "objectRelationsStabilityRatio", kind: "ratio", coef: 1.0, label_ko: "대상관계 · 내적대상", wave: "psychodynamic" },
  { id: "selfPsychologyScore", school: "SELF_PSYCHOLOGY", raw: "selfPsychologyMirroringRatio", kind: "ratio", coef: 1.0, label_ko: "자기심리학 · 미러링", wave: "psychodynamic" },
  { id: "taScriptScore", school: "TRANSACTIONAL_ANALYSIS", raw: "taAdultEgoRatio", kind: "ratio", coef: 1.0, label_ko: "TA · 성인자아", wave: "psychodynamic" },
  { id: "narrativeExternalizeScore", school: "NARRATIVE", raw: "narrativeExternalizationRatio", kind: "ratio", coef: 1.0, label_ko: "서사치료 · 외재화", wave: "systemic" },
  { id: "iptRoleScore", school: "IPT", raw: "iptInterpersonalRepairRatio", kind: "ratio", coef: 1.0, label_ko: "IPT · 관계회복", wave: "systemic" },
  { id: "bowenDifferentiationScore", school: "BOWEN_SYSTEMS", raw: "bowenDifferentiationRatio", kind: "ratio", coef: 1.0, label_ko: "보웬 · 분화", wave: "systemic" },
  { id: "structuralBoundaryScore", school: "STRUCTURAL_FAMILY", raw: "structuralBoundaryClarityRatio", kind: "ratio", coef: 1.0, label_ko: "구조가족 · 경계", wave: "systemic" },
  { id: "satirCongruenceScore", school: "SATIR", raw: "satirCongruenceRatio", kind: "ratio", coef: 1.0, label_ko: "사티어 · 일치소통", wave: "systemic" },
  { id: "strategicReframeScore", school: "STRATEGIC_FAMILY", raw: "strategicReframeSuccessRatio", kind: "ratio", coef: 1.0, label_ko: "전략가족 · 재구성", wave: "systemic" },
  { id: "attachmentSecureScore", school: "ATTACHMENT", raw: "attachmentSecureBaseRatio", kind: "ratio", coef: 1.0, label_ko: "애착 · 안전기지", wave: "systemic" },
  { id: "eftBondScore", school: "EFT", raw: "eftEmotionalBondRatio", kind: "ratio", coef: 1.0, label_ko: "EFT · 정서유대", wave: "systemic" },
  { id: "miChangeTalkScore", school: "MOTIVATIONAL", raw: "miChangeTalkRatio", kind: "ratio", coef: 1.0, label_ko: "MI · 변화대화", wave: "brief_trauma" },
  { id: "traumaSafetyScore", school: "TRAUMA_INFORMED", raw: "traumaSafetyCueRatio", kind: "ratio", coef: 1.0, label_ko: "트라우마정보 · 안전", wave: "brief_trauma" },
  { id: "emdrStabilizeScore", school: "EMDR_INFORMED", raw: "emdrStabilizationRatio", kind: "ratio", coef: 1.0, label_ko: "EMDR안내 · 안정화", wave: "brief_trauma" },
  { id: "ifsSelfLeadershipScore", school: "IFS", raw: "ifsSelfLeadershipRatio", kind: "ratio", coef: 1.0, label_ko: "IFS · Self리더십", wave: "brief_trauma" },
  { id: "cptStuckPointScore", school: "CPT_INFORMED", raw: "cptStuckPointShiftMs", kind: "latency", coef: 0.04, label_ko: "CPT안내 · stuck point", wave: "brief_trauma" },
  { id: "seTitrationScore", school: "SOMATIC_EXPERIENCING", raw: "seTitrationSafetyRatio", kind: "ratio", coef: 1.0, label_ko: "SE안내 · 타이틀레이션", wave: "brief_trauma" },
  { id: "peApproachScore", school: "PROLONGED_EXPOSURE_INFORMED", raw: "peGradualApproachRatio", kind: "ratio", coef: 1.0, label_ko: "PE안내 · 점진접근", wave: "brief_trauma" },
  { id: "psychodramaRoleScore", school: "PSYCHODRAMA", raw: "psychodramaRoleFlexibilityRatio", kind: "ratio", coef: 1.0, label_ko: "심리극 · 역할유연", wave: "expressive" },
  { id: "dramaTherapyScore", school: "DRAMA_THERAPY", raw: "dramaTherapyExpressionRatio", kind: "ratio", coef: 1.0, label_ko: "연극치료 · 표현", wave: "expressive" },
  { id: "artTherapyScore", school: "ART_THERAPY", raw: "artTherapySymbolFluencyRatio", kind: "ratio", coef: 1.0, label_ko: "미술치료 · 상징유창", wave: "expressive" },
  { id: "musicTherapyScore", school: "MUSIC_THERAPY", raw: "musicTherapyAttunementRatio", kind: "ratio", coef: 1.0, label_ko: "음악치료 · 조율", wave: "expressive" },
  { id: "danceMovementScore", school: "DANCE_MOVEMENT", raw: "danceMovementEmbodimentRatio", kind: "ratio", coef: 1.0, label_ko: "무용치료 · 체화", wave: "expressive" },
  { id: "playTherapyScore", school: "PLAY_THERAPY", raw: "playTherapySpontaneityRatio", kind: "ratio", coef: 1.0, label_ko: "놀이치료 · 자발성", wave: "expressive" },
  { id: "sandplayScore", school: "SANDPLAY", raw: "sandplaySceneCoherenceRatio", kind: "ratio", coef: 1.0, label_ko: "모래놀이 · 장면응집", wave: "expressive" },
  { id: "mindfulnessScore", school: "MINDFULNESS", raw: "mindfulnessPresentMomentRatio", kind: "ratio", coef: 1.0, label_ko: "마음챙김 · 현재", wave: "integrative" },
  { id: "feministEmpowerScore", school: "FEMINIST", raw: "feministEmpowermentRatio", kind: "ratio", coef: 1.0, label_ko: "페미니스트 · 임파워", wave: "integrative" },
  { id: "multiculturalHumilityScore", school: "MULTICULTURAL", raw: "multiculturalHumilityRatio", kind: "ratio", coef: 1.0, label_ko: "다문화 · 겸손", wave: "integrative" },
  { id: "polyvagalSafetyScore", school: "POLYVAGAL_INFORMED", raw: "polyvagalSafetySignalRatio", kind: "ratio", coef: 1.0, label_ko: "다미주 · 안전신호", wave: "integrative" },
  { id: "integrativeFitScore", school: "INTEGRATIVE", raw: "integrativeTechniqueFitRatio", kind: "ratio", coef: 1.0, label_ko: "통합 · 맞춤적합", wave: "integrative" },
  { id: "relapsePreventionScore", school: "RELAPSE_PREVENTION", raw: "relapseHighRiskCopingRatio", kind: "ratio", coef: 1.0, label_ko: "재발예방 · 고위험대처", wave: "addiction" },
  { id: "contingencyScore", school: "CONTINGENCY_MANAGEMENT", raw: "contingencyRewardFollowThroughRatio", kind: "ratio", coef: 1.0, label_ko: "유관관리 · 보상이행", wave: "addiction" },
  { id: "craScore", school: "CRA_COMMUNITY", raw: "craCommunitySupportRatio", kind: "ratio", coef: 1.0, label_ko: "CRA · 지역지원", wave: "addiction" },
  { id: "craftScore", school: "CRAFT_FAMILY", raw: "craftFamilyInviteRatio", kind: "ratio", coef: 1.0, label_ko: "CRAFT · 가족초대", wave: "addiction" },
  { id: "twelveStepScore", school: "TWELVE_STEP_FACILITATION", raw: "twelveStepMeetingEngagementRatio", kind: "ratio", coef: 1.0, label_ko: "12단계 · 모임참여", wave: "addiction" },
  { id: "matrixScore", school: "MATRIX_MODEL", raw: "matrixStructureAdherenceRatio", kind: "ratio", coef: 1.0, label_ko: "매트릭스 · 구조이행", wave: "addiction" },
  { id: "harmReductionScore", school: "HARM_REDUCTION", raw: "harmReductionSafetyPlanRatio", kind: "ratio", coef: 1.0, label_ko: "위해감축 · 안전계획", wave: "addiction" },
  { id: "smartRecoveryScore", school: "SMART_RECOVERY", raw: "smartRecoveryToolUseRatio", kind: "ratio", coef: 1.0, label_ko: "SMART · 도구사용", wave: "addiction" },
  { id: "addictionCbtScore", school: "ADDICTION_CBT", raw: "addictionCbtUrgeSurfMs", kind: "latency", coef: 0.05, label_ko: "중독CBT · 욕구서핑", wave: "addiction" },
  { id: "cravingMindfulnessScore", school: "CRAVING_MINDFULNESS", raw: "cravingMindfulnessObserveRatio", kind: "ratio", coef: 1.0, label_ko: "갈망챙김 · 관찰", wave: "addiction" },
];

/** @deprecated use THERAPY_AXIS_SPECS — kept for classic UI */
export const THERAPY_AXES = THERAPY_AXIS_SPECS.filter((a) => a.wave === "classic").map((a) => ({
  id: a.id,
  theory: a.school.toLowerCase(),
  label_ko: a.label_ko,
}));

function clamp01to100(n: number): number {
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(100, n));
}

function round1(n: number): number {
  return Math.round(n * 10) / 10;
}

function defaultFor(kind: ScoreKind): number {
  if (kind === "ratio") return 0.5;
  if (kind === "duration") return 8;
  if (kind === "error") return 2;
  if (kind === "boost") return 5;
  return 600;
}

function scoreAxis(kind: ScoreKind, value: number, coef: number): number {
  if (kind === "latency") return clamp01to100(100 - value * coef);
  if (kind === "duration") return clamp01to100(value * coef);
  if (kind === "ratio") return clamp01to100(value * 100);
  if (kind === "error") return clamp01to100(100 - Math.abs(value) * coef);
  if (kind === "boost") return clamp01to100(value * coef);
  return 50;
}

export class TherapyEngineCalculator {
  public extractTherapyVector(userId: string, raw: TherapyBiomarkerRaw): TherapyProfileVector {
    const scores: TherapyProfileVector = { userId, non_diagnostic: true } as TherapyProfileVector;
    const bySchool: Record<string, number> = {};
    for (const spec of THERAPY_AXIS_SPECS) {
      const value = Number(raw[spec.raw] ?? defaultFor(spec.kind));
      let score = round1(scoreAxis(spec.kind, value, spec.coef));
      if (spec.id === "solutionScore") score = Math.round(score);
      (scores as Record<string, unknown>)[spec.id] = score;
      bySchool[spec.school] = score;
    }
    scores.bySchool = bySchool;
    scores.axisCount = THERAPY_AXIS_SPECS.length;
    return scores;
  }

  public topSchools(vector: TherapyProfileVector, limit = 5) {
    const entries = Object.entries(vector.bySchool || {});
    return entries
      .sort((a, b) => b[1] - a[1])
      .slice(0, Math.max(1, limit))
      .map(([school, score]) => {
        const spec = THERAPY_AXIS_SPECS.find((s) => s.school === school);
        return {
          school,
          score,
          label_ko: spec?.label_ko || school,
          wave: spec?.wave || "",
        };
      });
  }

  public calculateTherapeuticSynergy(
    userA: TherapyProfileVector,
    userB: TherapyProfileVector
  ): TherapeuticSynergyResult {
    const n = (v: unknown, d = 50) => (typeof v === "number" && Number.isFinite(v) ? v : d);
    const cognitiveHarmony = 100 - Math.abs(n(userA.cbtShiftScore) - n(userB.cbtShiftScore));
    const solutionSynergy = (n(userA.solutionScore) + n(userB.solutionScore)) / 2;
    const courageBalance = Math.abs(n(userA.courageScore) - n(userB.courageScore));
    const complementAlpha = 100 - Math.abs(courageBalance - 30);

    const aDbt = n(userA.dbtRegulationScore);
    const bDbt = n(userB.dbtRegulationScore);
    const aAct = n(userA.actValuesScore);
    const bAct = n(userB.actValuesScore);
    const aTrauma = n(userA.traumaSafetyScore);
    const bTrauma = n(userB.traumaSafetyScore);
    const modernHarmony =
      (100 - Math.abs(aDbt - bDbt)) * 0.34 +
      ((aAct + bAct) / 2) * 0.33 +
      ((aTrauma + bTrauma) / 2) * 0.33;

    const classic = cognitiveHarmony * 0.4 + solutionSynergy * 0.3 + complementAlpha * 0.3;
    const finalTherapyMatchScore = Math.round(classic * 0.7 + modernHarmony * 0.3);

    let primaryTherapeuticType = "인지적 유연형 파트너";
    if (n(userA.solutionScore) > 70) primaryTherapeuticType = "해결중심적 스페셜리스트";
    else if (aAct > 70) primaryTherapeuticType = "ACT 가치전념형 파트너";
    else if (aDbt > 70) primaryTherapeuticType = "DBT 감정조절형 파트너";

    return {
      finalTherapyMatchScore,
      primaryTherapeuticType,
      recommendedTherapyIcebreaker:
        `두 분은 [해결중심 + CBT + 최신(DBT/ACT/트라우마안전)] 상성 알파 ${finalTherapyMatchScore}점입니다. ` +
        "위기 상황에서 서로의 인지·감정조절·가치를 보완해 주는 조합이에요!",
      components: {
        cognitiveHarmony: round1(cognitiveHarmony),
        solutionSynergy: round1(solutionSynergy),
        complementAlpha: round1(complementAlpha),
        modernHarmony: round1(modernHarmony),
      },
      topSchoolsA: this.topSchools(userA, 3),
      topSchoolsB: this.topSchools(userB, 3),
      non_diagnostic: true,
    };
  }
}

export default TherapyEngineCalculator;
