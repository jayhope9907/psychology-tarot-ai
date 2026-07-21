/**
 * IntegratedDiagnosticModel — CognitiveProfile + clinicalProfile + 3D 렌더 힌트 계약.
 *
 * Backend source of truth:
 *   - app/services/emotional_spectrum.py → to_integrated_diagnostic_model()
 *   - SSE `done` payload key `integrated_diagnostic_model`
 *   - GET /api/v1/users/{user_id}/integrated-diagnostic
 */
import type { DownstreamTriggers, InternalizingRiskLevel } from "./DSM5IntegratedDiagnostic";

export interface InternalizingCore {
  total_internalizing_score: number;
  internalizing_risk_level: InternalizingRiskLevel;
  downstream_triggers?: DownstreamTriggers | null;
}

export interface CognitiveProfile {
  // CHC 이론 기반 5대 지능 축 (0 ~ 150 표준점수 기준 변환)
  g_factor: number; // 전체 지능 (FSIQ)
  crystallized_gc: number; // 언어이해 (Gc)
  fluid_gf: number; // 지각추론/유동추론 (Gf)
  working_memory_gwm: number; // 작업기억 (Gwm)
  processing_speed_gs: number; // 처리속도 (Gs)
  visual_processing_gv: number; // 시공간 (Gv)
}

export interface IntegratedDiagnosticModel {
  sessionId: string;
  patientId: string;
  internalizing_core?: InternalizingCore;
  cognitiveProfile: CognitiveProfile; // 뼈대 (그릇의 크기)
  clinicalProfile: {
    schizophrenia_index: number;
    asd_stimming_index: number;
    depression_index: number;
  };
  threeRenderMetrics: {
    backbone_tension: number; // 지능 뼈대 탄성도 (낮을수록 인지 와해)
    cluster_density: number; // 자폐 고착화 노드 밀집도
  };
}

