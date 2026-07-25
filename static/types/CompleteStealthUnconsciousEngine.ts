// ============================================================================
// PROJECT: Now You See Me - Ultimate Unconscious Mapping Engine (v5.1 Refined)
// ARCHITECTURE: 11-Prop Gamification + Movie-cation + Clinical IDE Pipeline
// FILE: CompleteStealthUnconsciousEngine.ts
//
// Backend source of truth (동일 계수/동일 결과):
//   - app/services/stealth_unconscious_engine.py
//   - POST /api/v1/users/{user_id}/stealth-unconscious/ingest
//   - GET  /api/v1/users/{user_id}/stealth-unconscious
//   - GET  /api/v1/stealth-unconscious/props
//
// 비진단 웰니스 참고 지표 (non_diagnostic). 의료적 진단 대체 목적 아님.
// ============================================================================

import type { IntegratedDiagnosticModel } from "./IntegratedDiagnosticModel";

export type PropType =
  | 'RAIN_DROP'           // 1. 물방울 (주파수 동기화)
  | 'WATER_TANK'          // 2. 수조 (수쇄 탈출 QTE)
  | 'CARD_STEALTH'        // 3. 카드 (레이저 스텔스 패스)
  | 'CHAMBER_BOX'         // 4. 상자 (차원 반전)
  | 'MIRROR_SHADOW'       // 5. 미러 (가짜 잔상 관조)
  | 'ROULETTE_DIAL'       // 6. 루렛 (시선 유도 미스디렉션)
  | 'PERSONA_MASK'        // 7. 페르소나 마스크 (변장 및 미세표정)
  | 'SLEIGHT_PALMING'     // 8. 손놀림 (미세 제스처/터치 압력)
  | 'MENTAL_PRIMING'      // 9. 멘탈리즘 (암시 수용성/무의식 프라이밍)
  | 'HOLOGRAM_REALITY'    // 10. 홀로그램 (지각적 현실 검증력 및 정보 왜곡 저항성)
  | 'INTERPERSONAL_SYNC'; // 11. 인터랙션 동기화 (대인 인지 동기화 및 상호작용 유연성)

export const PROP_TYPES: PropType[] = [
  'RAIN_DROP',
  'WATER_TANK',
  'CARD_STEALTH',
  'CHAMBER_BOX',
  'MIRROR_SHADOW',
  'ROULETTE_DIAL',
  'PERSONA_MASK',
  'SLEIGHT_PALMING',
  'MENTAL_PRIMING',
  'HOLOGRAM_REALITY',
  'INTERPERSONAL_SYNC',
];

export type HorsemenPersona = 'DANIEL_ATLAS' | 'MERRITT_MCKINNEY' | 'JACK_WILDER' | 'HENLEY_REEVES';

// 0.01초 단위 생체/행동 원시 Payload 데이터
export interface RawBiomarkerPayload {
  prop: PropType;
  timestampMs: number;

  // [1. 물방울]
  strobePrecisionDeltaPx?: number;
  tremorVector?: { x: number; y: number; z?: number };

  // [2. 수조]
  qteLatencyMs?: number;
  panicStimmingCount?: number;

  // [3. 카드]
  stealthPassLatencyMs?: number;
  trajectoryAccuracyRatio?: number;

  // [4. 상자]
  rigidPatternRepeatCount?: number;
  dimensionReconstructTimeSec?: number;

  // [5. 미러]
  illusionChasingClicks?: number;
  idleAcceptanceDurationMs?: number;

  // [6. 루렛]
  misdirectionBaitClicks?: number;
  entropyRandomnessIndex?: number;

  // [7. 마스크]
  microExpressionScanLatencyMs?: number;
  maskMatchAccuracyRatio?: number;

  // [8. 손놀림]
  gestureCurvatureVariance?: number;
  touchPressureInstability?: number;

  // [9. 멘탈리즘]
  primingBiasAcceptanceRatio?: number;
  decisionHesitationMs?: number;

  // [10. 홀로그램] 정교한 착시 자극에 대한 피낚임 횟수 및 지각적 현실 검증력 점수
  distortionIllusionChasingClicks?: number;
  perceptualRealityTestingScore?: number; // 0 ~ 100 (높을수록 지각적 탈융합 및 현실 검증력 우수)

  // [11. 인터랙션 동기화] 상호작용 상대와의 반응 타이밍 오차 및 대인 인지 동기화 비율
  interpersonalSyncDeltaMs?: number;
  socialAdaptabilityRatio?: number; // 0.0 ~ 1.0
}

// CHC 지능 프로파일
export interface CHCProfile {
  Gv: number;  // 시공간 처리 지능
  Gs: number;  // 인지 처리 속도
  Gwm: number; // 작업 기억 용량
  Gc: number;  // 결정성/사회적 맥락 지능
}

// DSM/임상 바이오마커 프로파일
export interface ClinicalBiomarkerProfile {
  ocdRigidityScore: number;         // 강박성/고착 지표
  panicAnxietyIndex: number;        // 공황/신체화 떨림 지표
  asdStimmingRate: number;          // 자폐적/자가자극 연타 지표
  dissociationScore: number;        // 해리/현실검증력 저하 지표
  cognitiveFlexibility: number;     // 인지적 유연성
  impulsivityMisdirection: number;  // 충동성 및 시선 유도 피낚임 지표
  empathyTheoryOfMind: number;      // 마음 이론/타인 표정 감지 지표
  personaIdentityFluidity: number;  // 자아 페르소나 가변성 지표
  fineMotorControlIndex: number;    // 미세 운동 조율 및 터치 안정성
  hypnoticSuggestibility: number;   // 암시 수용성 및 점침성 지표
  perceptualDefusionIndex: number;  // 지각적 현실 검증력 및 착시 탈융합 지표
  interpersonalSynchrony: number;   // 대인 관계적 인지 동기화 지표
}

// 최종 평가 결과 인터페이스
export interface HorsemenPersonaResult {
  persona: HorsemenPersona;
  title: string;
  awakeningQuote: string;
  stats: {
    spatialControl: number;
    mindReading: number;
    sleightSpeed: number;
    escapeResilience: number;
    personaDisguise: number;
    mentalSuggestibility: number;
    perceptualRealityTesting: number; // 지각적 현실 검증력 스탯
    interpersonalSynergy: number;     // 대인 인지 동기화 스탯
  };
  chcProfile: CHCProfile;
  clinicalProfile: ClinicalBiomarkerProfile;
  clinicalIDEOutput: string;
  /** MindNetwork3D Future Projection 브리지 (백엔드가 함께 반환) */
  integrated_diagnostic_model?: IntegratedDiagnosticModel;
  non_diagnostic?: true;
}

// ----------------------------------------------------------------------------
// Master 11-Prop Biomarker Evaluator
// ----------------------------------------------------------------------------

export class Master11PropEvaluator {

  public evaluateRainDrop(p: RawBiomarkerPayload) {
    const delta = p.strobePrecisionDeltaPx ?? 10.0;
    const tv = p.tremorVector ?? { x: 0, y: 0, z: 0 };
    const euclideanTremor = Math.sqrt(tv.x ** 2 + tv.y ** 2 + (tv.z ?? 0) ** 2);
    return {
      ocdRigidity: Math.min(100, Math.max(0, 100 - delta * 8.5)),
      panicAnxiety: Math.min(100, euclideanTremor * 18.2),
      gvContribution: Math.min(100, Math.max(0, 100 - delta * 4.2))
    };
  }

  public evaluateWaterTank(p: RawBiomarkerPayload) {
    const qteLatency = p.qteLatencyMs ?? 1200;
    const stimming = p.panicStimmingCount ?? 0;
    const gwmScore = 100 * Math.exp(-0.0018 * Math.max(0, qteLatency - 150));
    return {
      panicIndex: Math.min(100, stimming * 9.5),
      stimmingRate: stimming,
      gwmContribution: Math.min(100, Math.max(0, gwmScore))
    };
  }

  public evaluateCardStealth(p: RawBiomarkerPayload) {
    const latency = p.stealthPassLatencyMs ?? 900;
    const accuracy = p.trajectoryAccuracyRatio ?? 0.5;
    const gsScore = 100 * Math.exp(-0.0022 * Math.max(0, latency - 120));
    return {
      gsContribution: Math.min(100, Math.max(0, gsScore)),
      gvContribution: accuracy * 100
    };
  }

  public evaluateChamberBox(p: RawBiomarkerPayload) {
    const repeats = p.rigidPatternRepeatCount ?? 0;
    const sec = p.dimensionReconstructTimeSec ?? 40;
    return {
      cognitiveFlexibility: Math.max(0, 100 - (repeats * 14.5 + sec * 1.8)),
      gcContribution: Math.min(100, Math.max(0, 95 - repeats * 9.0))
    };
  }

  public evaluateMirrorShadow(p: RawBiomarkerPayload) {
    const chasingClicks = p.illusionChasingClicks ?? 0;
    const idleTime = p.idleAcceptanceDurationMs ?? 0;
    return {
      dissociationScore: Math.min(100, chasingClicks * 16.5),
      realityTestingScore: Math.min(100, Math.max(0, (idleTime / 3000) * 100))
    };
  }

  public evaluateRouletteDial(p: RawBiomarkerPayload) {
    const baitClicks = p.misdirectionBaitClicks ?? 0;
    const entropy = p.entropyRandomnessIndex ?? 0.5;
    return {
      impulsivityIndex: Math.min(100, baitClicks * 22.0 + (1.0 - entropy) * 30.0),
      gcContribution: Math.min(100, Math.max(0, entropy * 100))
    };
  }

  public evaluatePersonaMask(p: RawBiomarkerPayload) {
    const scanLatency = p.microExpressionScanLatencyMs ?? 1000;
    const accuracy = p.maskMatchAccuracyRatio ?? 0.5;
    const empathy = accuracy * 100 * Math.exp(-0.001 * Math.max(0, scanLatency - 200));
    return {
      empathyTheoryOfMind: Math.min(100, Math.max(0, empathy)),
      gcContribution: Math.min(100, Math.max(0, empathy))
    };
  }

  public evaluateSleightPalming(p: RawBiomarkerPayload) {
    const curvature = p.gestureCurvatureVariance ?? 0.5;
    const pressureInstability = p.touchPressureInstability ?? 0.4;
    const fineMotor = Math.max(0, 100 - (curvature * 40 + pressureInstability * 50));
    return {
      fineMotorControlIndex: Math.min(100, fineMotor),
      gsContribution: Math.min(100, fineMotor)
    };
  }

  public evaluateMentalPriming(p: RawBiomarkerPayload) {
    const suggestibility = p.primingBiasAcceptanceRatio ?? 0.5;
    const hesitation = p.decisionHesitationMs ?? 1000;
    return {
      hypnoticSuggestibility: Math.min(100, suggestibility * 100),
      gcContribution: Math.min(100, 100 * Math.exp(-0.001 * Math.max(0, hesitation - 300)))
    };
  }

  // 10. 홀로그램: 지각적 현실 검증력 (Perceptual Reality Testing) 및 착시 탈융합
  public evaluateHologramReality(p: RawBiomarkerPayload) {
    const chasingClicks = p.distortionIllusionChasingClicks ?? 0;
    const baseTestingScore = p.perceptualRealityTestingScore ?? 50;
    const realityTesting = Math.max(0, baseTestingScore - chasingClicks * 12.0);
    return {
      perceptualDefusionIndex: Math.min(100, realityTesting),
      gvContribution: Math.min(100, realityTesting)
    };
  }

  // 11. 인터랙션 동기화: 대인 인지 동기화 (Interpersonal Cognitive Synchrony) 및 유연성
  public evaluateInterpersonalSync(p: RawBiomarkerPayload) {
    const deltaMs = p.interpersonalSyncDeltaMs ?? 500;
    const adaptability = p.socialAdaptabilityRatio ?? 0.5;
    const synchroScore = adaptability * 100 * Math.exp(-0.002 * Math.max(0, deltaMs - 50));
    return {
      interpersonalSynchrony: Math.min(100, Math.max(0, synchroScore)),
      gwmContribution: Math.min(100, Math.max(0, synchroScore))
    };
  }
}

// ----------------------------------------------------------------------------
// Full Engine Orchestrator
// ----------------------------------------------------------------------------

export class FullUnconsciousEngine {
  private evaluator = new Master11PropEvaluator();

  private aggregateCHC: CHCProfile = { Gv: 50, Gs: 50, Gwm: 50, Gc: 50 };
  private aggregateClinical: ClinicalBiomarkerProfile = {
    ocdRigidityScore: 0,
    panicAnxietyIndex: 0,
    asdStimmingRate: 0,
    dissociationScore: 0,
    cognitiveFlexibility: 50,
    impulsivityMisdirection: 0,
    empathyTheoryOfMind: 50,
    personaIdentityFluidity: 50,
    fineMotorControlIndex: 50,
    hypnoticSuggestibility: 50,
    perceptualDefusionIndex: 50,
    interpersonalSynchrony: 50
  };

  private ingestedProps = new Set<PropType>();

  public ingestBiomarker(payload: RawBiomarkerPayload): void {
    this.ingestedProps.add(payload.prop);
    switch (payload.prop) {
      case 'RAIN_DROP': {
        const res = this.evaluator.evaluateRainDrop(payload);
        this.aggregateClinical.ocdRigidityScore = res.ocdRigidity;
        this.aggregateClinical.panicAnxietyIndex = (this.aggregateClinical.panicAnxietyIndex + res.panicAnxiety) / 2;
        this.aggregateCHC.Gv = (this.aggregateCHC.Gv + res.gvContribution) / 2;
        break;
      }
      case 'WATER_TANK': {
        const res = this.evaluator.evaluateWaterTank(payload);
        this.aggregateClinical.panicAnxietyIndex = (this.aggregateClinical.panicAnxietyIndex + res.panicIndex) / 2;
        this.aggregateClinical.asdStimmingRate = res.stimmingRate;
        this.aggregateCHC.Gwm = (this.aggregateCHC.Gwm + res.gwmContribution) / 2;
        break;
      }
      case 'CARD_STEALTH': {
        const res = this.evaluator.evaluateCardStealth(payload);
        this.aggregateCHC.Gs = (this.aggregateCHC.Gs + res.gsContribution) / 2;
        this.aggregateCHC.Gv = (this.aggregateCHC.Gv + res.gvContribution) / 2;
        break;
      }
      case 'CHAMBER_BOX': {
        const res = this.evaluator.evaluateChamberBox(payload);
        this.aggregateClinical.cognitiveFlexibility = res.cognitiveFlexibility;
        this.aggregateCHC.Gc = (this.aggregateCHC.Gc + res.gcContribution) / 2;
        break;
      }
      case 'MIRROR_SHADOW': {
        const res = this.evaluator.evaluateMirrorShadow(payload);
        this.aggregateClinical.dissociationScore = res.dissociationScore;
        // 잔상 관조 시간이 길수록 페르소나 관찰 유연성이 높아지는 방향
        this.aggregateClinical.personaIdentityFluidity =
          (this.aggregateClinical.personaIdentityFluidity + res.realityTestingScore) / 2;
        break;
      }
      case 'ROULETTE_DIAL': {
        const res = this.evaluator.evaluateRouletteDial(payload);
        this.aggregateClinical.impulsivityMisdirection = res.impulsivityIndex;
        this.aggregateCHC.Gc = (this.aggregateCHC.Gc + res.gcContribution) / 2;
        break;
      }
      case 'PERSONA_MASK': {
        const res = this.evaluator.evaluatePersonaMask(payload);
        this.aggregateClinical.empathyTheoryOfMind = res.empathyTheoryOfMind;
        this.aggregateCHC.Gc = (this.aggregateCHC.Gc + res.gcContribution) / 2;
        break;
      }
      case 'SLEIGHT_PALMING': {
        const res = this.evaluator.evaluateSleightPalming(payload);
        this.aggregateClinical.fineMotorControlIndex = res.fineMotorControlIndex;
        this.aggregateCHC.Gs = (this.aggregateCHC.Gs + res.gsContribution) / 2;
        break;
      }
      case 'MENTAL_PRIMING': {
        const res = this.evaluator.evaluateMentalPriming(payload);
        this.aggregateClinical.hypnoticSuggestibility = res.hypnoticSuggestibility;
        this.aggregateCHC.Gc = (this.aggregateCHC.Gc + res.gcContribution) / 2;
        break;
      }
      case 'HOLOGRAM_REALITY': {
        const res = this.evaluator.evaluateHologramReality(payload);
        this.aggregateClinical.perceptualDefusionIndex = res.perceptualDefusionIndex;
        this.aggregateCHC.Gv = (this.aggregateCHC.Gv + res.gvContribution) / 2;
        break;
      }
      case 'INTERPERSONAL_SYNC': {
        const res = this.evaluator.evaluateInterpersonalSync(payload);
        this.aggregateClinical.interpersonalSynchrony = res.interpersonalSynchrony;
        this.aggregateCHC.Gwm = (this.aggregateCHC.Gwm + res.gwmContribution) / 2;
        break;
      }
    }
  }

  public getProgress(): { ingested: PropType[]; remaining: PropType[]; completionRatio: number } {
    const ingested = PROP_TYPES.filter((p) => this.ingestedProps.has(p));
    const remaining = PROP_TYPES.filter((p) => !this.ingestedProps.has(p));
    return {
      ingested,
      remaining,
      completionRatio: ingested.length / PROP_TYPES.length,
    };
  }

  public finalizePersonaAssessment(): HorsemenPersonaResult {
    const { Gv, Gs, Gwm, Gc } = this.aggregateCHC;
    const cli = this.aggregateClinical;

    let persona: HorsemenPersona = 'DANIEL_ATLAS';
    let title = '환영의 통제자 (Illusion Architect)';
    let awakeningQuote = '가장 완벽한 환상은 통제되고 있다는 감각 그 자체입니다.';

    if (cli.perceptualDefusionIndex > 75 && Gv > 80) {
      persona = 'DANIEL_ATLAS';
      title = '현실 검증의 설계자 (Master Reality-Architect)';
      awakeningQuote = '외부의 인지적 자극과 정보 왜곡 속에서도 명확한 실체를 꿰뚫어 보는 자입니다.';
    } else if (cli.interpersonalSynchrony > 75 && cli.empathyTheoryOfMind > 70) {
      persona = 'MERRITT_MCKINNEY';
      title = '공감과 동기화의 멘탈리스트 (Synchro Mentalist)';
      awakeningQuote = '상대의 언어와 찰나의 타이밍을 완벽하게 읽어내어 대인적 동기화를 이룹니다.';
    } else if (cli.fineMotorControlIndex > 80 && Gs > 75) {
      persona = 'JACK_WILDER';
      title = '초감각 손놀림 마술사 (Sleight Master)';
      awakeningQuote = 'Always be the fastest in the room. 당신의 속도는 의식을 능가합니다.';
    } else {
      persona = 'HENLEY_REEVES';
      title = '탈출의 아티스트 (Escape Artist)';
      awakeningQuote = '가장 깊은 압박 속에서도 스스로 빠져나올 열쇠를 찾아냅니다.';
    }

    const clinicalIDEOutput = `
[CLINICAL IDE :: STEALTH PARSING REPORT]
------------------------------------------------------------------
TIMESTAMP           : ${new Date().toISOString()}
SESSION TARGET      : USER_UNCONSCIOUS_VECTOR
ASSIGNED PERSONA    : ${persona} (${title})
------------------------------------------------------------------
[CHC INTELLIGENCE PROFILE]
- Gv (Spatial Processing)         : ${Gv.toFixed(2)} / 100
- Gs (Processing Speed)           : ${Gs.toFixed(2)} / 100
- Gwm (Working Memory)            : ${Gwm.toFixed(2)} / 100
- Gc (Crystallized / Social)      : ${Gc.toFixed(2)} / 100

[DSM / CLINICAL SPECTRUM METRICS]
- OCD Rigidity Index              : ${cli.ocdRigidityScore.toFixed(2)} [${cli.ocdRigidityScore > 60 ? 'HIGH' : 'NORMAL'}]
- Somatic Panic / Tremor          : ${cli.panicAnxietyIndex.toFixed(2)} [${cli.panicAnxietyIndex > 50 ? 'ELEVATED' : 'STABLE'}]
- ASD Motor Stimming Rate         : ${cli.asdStimmingRate} CPM
- Dissociation / Reality Score    : ${(100 - cli.dissociationScore).toFixed(2)}% [REALITY_TESTING]
- Misdirection Impulsivity        : ${cli.impulsivityMisdirection.toFixed(2)} [${cli.impulsivityMisdirection > 55 ? 'HIGH_SUSCEPTIBILITY' : 'STABLE'}]
- Fine Motor Precision            : ${cli.fineMotorControlIndex.toFixed(2)} [SLEIGHT_CONTROL]
- Hypnotic Suggestibility         : ${cli.hypnoticSuggestibility.toFixed(2)} [PRIMING_BIAS]
- Perceptual Reality Testing      : ${cli.perceptualDefusionIndex.toFixed(2)} [${cli.perceptualDefusionIndex > 70 ? 'HIGH_REALITY_TESTING' : 'SUSCEPTIBLE'}]
- Interpersonal Synchrony Rate    : ${cli.interpersonalSynchrony.toFixed(2)} [COGNITIVE_SYNCHRONY]
------------------------------------------------------------------`;

    return {
      persona,
      title,
      awakeningQuote,
      stats: {
        spatialControl: Math.round(Gv),
        sleightSpeed: Math.round(Gs),
        escapeResilience: Math.round(Gwm),
        mindReading: Math.round(Gc),
        personaDisguise: Math.round((cli.empathyTheoryOfMind + cli.personaIdentityFluidity) / 2),
        mentalSuggestibility: Math.round(cli.hypnoticSuggestibility),
        perceptualRealityTesting: Math.round(cli.perceptualDefusionIndex),
        interpersonalSynergy: Math.round(cli.interpersonalSynchrony)
      },
      chcProfile: {
        Gv: Math.round(Gv),
        Gs: Math.round(Gs),
        Gwm: Math.round(Gwm),
        Gc: Math.round(Gc)
      },
      clinicalProfile: cli,
      clinicalIDEOutput,
      non_diagnostic: true
    };
  }
}

// ----------------------------------------------------------------------------
// MindNetwork3D Future Projection 브리지
// ----------------------------------------------------------------------------

/**
 * 11-프롭 결과 → MindNetwork3D `setDiagnostic()` 입력 계약.
 *
 * 백엔드 `to_integrated_diagnostic_model_from_persona()`와 동일 규칙:
 *   - CHC 0~100 → 표준점수 0~150 (× 1.5)
 *   - dissociationScore → schizophrenia_index (파편화/점선 링크)
 *   - ocdRigidityScore + asdStimmingRate → asd_stimming_index (고착 노드 밀집)
 */
export function toIntegratedDiagnosticModel(
  result: HorsemenPersonaResult,
  opts: { sessionId?: string; patientId?: string } = {}
): IntegratedDiagnosticModel {
  const chc = result.chcProfile;
  const cli = result.clinicalProfile;
  const clamp150 = (x: number) => Math.max(0, Math.min(150, x));
  const clamp100 = (x: number) => Math.max(0, Math.min(100, x));

  const gFactor = clamp150(((chc.Gv + chc.Gs + chc.Gwm + chc.Gc) / 4) * 1.5);
  const schizophreniaIndex = clamp100(
    cli.dissociationScore * 0.6 + (100 - cli.perceptualDefusionIndex) * 0.4
  );
  const asdStimmingIndex = clamp100(
    cli.ocdRigidityScore * 0.5 + Math.min(100, cli.asdStimmingRate * 9.5) * 0.5
  );
  const depressionIndex = clamp100(
    (100 - cli.cognitiveFlexibility) * 0.5 + cli.panicAnxietyIndex * 0.5
  );

  return {
    sessionId: opts.sessionId ?? "",
    patientId: opts.patientId ?? "",
    cognitiveProfile: {
      g_factor: gFactor,
      crystallized_gc: clamp150(chc.Gc * 1.5),
      fluid_gf: clamp150(((chc.Gv + chc.Gwm) / 2) * 1.5),
      working_memory_gwm: clamp150(chc.Gwm * 1.5),
      processing_speed_gs: clamp150(chc.Gs * 1.5),
      visual_processing_gv: clamp150(chc.Gv * 1.5),
    },
    clinicalProfile: {
      schizophrenia_index: schizophreniaIndex,
      asd_stimming_index: asdStimmingIndex,
      depression_index: depressionIndex,
    },
    threeRenderMetrics: {
      backbone_tension: clamp100((gFactor / 150) * 100 * (1 - schizophreniaIndex / 200)),
      cluster_density: clamp100(asdStimmingIndex * 0.7 + schizophreniaIndex * 0.3),
    },
  };
}
