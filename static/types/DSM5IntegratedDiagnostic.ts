/**
 * DSM5IntegratedDiagnostic — 통합 내재화 스펙트럼 계약 (비진단 참고 지표).
 *
 * Backend source of truth: app/services/emotional_spectrum.py
 *   → to_dsm5_integrated_diagnostic()
 * Delivered via:
 *   - SSE `done` payload key `dsm5_integrated_diagnostic`
 *   - POST/GET /api/v1/users/{user_id}/emotional-spectrum (`diagnostic`)
 */

export type InternalizingRiskLevel = 'NORMAL' | 'MONITOR' | 'HIGH_ALERT';
export type SuggestedClinicalApproach = 'PROST_CONFRONTATION' | 'SUNG_AH_SUPPORT';

export interface SchizophreniaSpectrum {
  loose_association: number;   // 연상 이완 지수 (0 - 100)
  thought_blocking: number;    // 사고 차단 지수 (0 - 100)
  ego_boundary_loss: number;   // 자아 경계 붕괴 (마인드맵 파편화 스코어)
  delusional_affinity: number; // 망상적 사고 친화도 (0 - 100)
}

export interface IntegratedDimensions {
  depressive_index: number;
  anxiety_index: number;
  obsessive_compulsive: number;
  panic_index: number;
  bipolar_fluctuation_index: number;
  somatic_symptom_index: number;
  schizophrenia_spectrum: SchizophreniaSpectrum;
}

export interface RoomProjection {
  color_tone: 'cold-white' | 'dark-gray' | 'warm-yellow' | 'fractured-distorted';
  lighting_level: number; // 0 - 100
  wall_symmetry: 'rigid' | 'natural' | 'broken';
}

export type DownstreamTrackRiskLevel = 'NORMAL' | 'ELEVATED';

export interface DepressionPanicTrackRisk {
  level: DownstreamTrackRiskLevel;
  trigger_internalizing_threshold: number;
  depression_bump: number;
  panic_bump: number;
}

export interface OcdAsdLoopIssueEvidence {
  total_internalizing_score: number;
  cognitive_rigidity_score: number;
  gs_slowdown_proxy: number;
  stimming_proxy: number;
  defensive_language_signal: number;
  panic_index: number;
  obsessive_compulsive_index: number;
}

export interface OcdAsdLoopIssue {
  code: 'OCD_ASD_LOOP';
  labelKo: string;
  severity: 'HIGH';
  evidence: OcdAsdLoopIssueEvidence;
}

export interface OcdAsdLoopDebugConsole {
  enabled: boolean;
  issues: OcdAsdLoopIssue[];
}

export interface DownstreamTriggers {
  depression_panic_track_risk: DepressionPanicTrackRisk;
  ocd_asd_loop: OcdAsdLoopDebugConsole;
}

export interface DSM5IntegratedDiagnostic {
  session_id: string;
  user_id: string;
  timestamp: string;

  // 1. 핵심 내재화(Internalizing) 스펙트럼 총합 지표
  total_internalizing_score: number;
  internalizing_risk_level: InternalizingRiskLevel;

  // Chained downstream triggers from InternalizingCoreEngine (explicit debug payload)
  downstream_triggers?: DownstreamTriggers | null;

  // 2. DSM-5 기반 다차원 스펙트럼 지수
  dimensions: IntegratedDimensions;

  // 3. 듀얼 AI 에이전트(프로스트/윤성아) 동적 스위칭 및 가상 방 인테리어 바인딩 변수
  clinical_meta: {
    suggested_approach: SuggestedClinicalApproach;
    room_projection: RoomProjection;
  };

  // 웰니스 참고 지표 플래그 (진단 아님)
  non_diagnostic: true;
}
