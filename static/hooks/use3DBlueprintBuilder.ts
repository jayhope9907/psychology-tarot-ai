/**
 * use3DBlueprintBuilder — React reference hook.
 *
 * On each user message, grows a force-graph-style blueprint:
 *   - extractKeyEmotionWord → 우울 궤적 / 자율신경 과활성 / 무의식 조각
 *   - NetworkNode sized by total_internalizing_score (>70 → val 15 else 8)
 *   - color HIGH_ALERT → #ff3333 else #10b981
 *   - link from center_self; ego_boundary_loss > 50 → #a855f7 else #06b6d4
 *   - dashed if loose_association > 60
 *
 * Chat UI uses static/js/blueprint-builder.js (vanilla). This file fixes the
 * TypeScript contract for React/Three consumers.
 */
import { useCallback, useRef, useState } from "react";
import type {
  DSM5IntegratedDiagnostic,
  InternalizingRiskLevel,
} from "../types/DSM5IntegratedDiagnostic";
import type { IntegratedDiagnosticModel } from "../types/IntegratedDiagnosticModel";

export type BlueprintDiagnostic =
  | DSM5IntegratedDiagnostic
  | IntegratedDiagnosticModel
  | Record<string, unknown>
  | null
  | undefined;

export interface NetworkNode {
  id: string;
  label: string;
  val: number;
  color: string;
  /** Force-graph / three.js optional position hints */
  x?: number;
  y?: number;
  z?: number;
}

export interface NetworkLink {
  source: string;
  target: string;
  color: string;
  dashed: boolean;
}

export interface BlueprintGraph {
  nodes: NetworkNode[];
  links: NetworkLink[];
}

export interface BlueprintMetrics {
  totalInternalizing: number;
  riskLevel: InternalizingRiskLevel | string;
  egoBoundaryLoss: number;
  looseAssociation: number;
}

const CENTER_ID = "center_self";
const MAX_HISTORY = 40;

const DEPRESSIVE_RE =
  /우울|가라앉|무기력|공허|슬프|희망\s*없|눈물|depress|sad|hopeless|empty/i;
const AUTONOMIC_RE =
  /불안|초조|긴장|두근|공황|숨\s*막|자율신경|과활성|심박|anxiety|panic|nervous|jitter/i;
const UNCONSCIOUS_RE =
  /꿈|무의식|환상|해리|와해|파편|연상|망상|이상한\s*생각|fragment|dream|dissoc|delusion/i;

function isIntegratedModel(data: BlueprintDiagnostic): data is IntegratedDiagnosticModel {
  return Boolean(
    data &&
      typeof data === "object" &&
      "clinicalProfile" in data &&
      (data as IntegratedDiagnosticModel).clinicalProfile
  );
}

function isDsm5(data: BlueprintDiagnostic): data is DSM5IntegratedDiagnostic {
  return Boolean(
    data &&
      typeof data === "object" &&
      "total_internalizing_score" in data &&
      "dimensions" in data
  );
}

/** Normalize DSM5 + IntegratedDiagnosticModel (+ loose neuro matrix) into shared metrics. */
export function parseBlueprintMetrics(diagnostic: BlueprintDiagnostic): BlueprintMetrics {
  const doc = (diagnostic || {}) as Record<string, unknown>;

  if (isIntegratedModel(diagnostic)) {
    const core = diagnostic.internalizing_core;
    const total =
      Number(core?.total_internalizing_score) ||
      Number((doc as { total_internalizing_score?: number }).total_internalizing_score) ||
      0;
    const risk =
      core?.internalizing_risk_level ||
      (total > 70 ? "HIGH_ALERT" : total > 40 ? "MONITOR" : "NORMAL");
    // schizophrenia_index → ego_boundary_loss / loose_association proxy
    const sch = Number(diagnostic.clinicalProfile?.schizophrenia_index) || 0;
    return {
      totalInternalizing: total,
      riskLevel: risk,
      egoBoundaryLoss: sch,
      looseAssociation: sch,
    };
  }

  if (isDsm5(diagnostic)) {
    const sch = diagnostic.dimensions?.schizophrenia_spectrum || {
      loose_association: 0,
      thought_blocking: 0,
      ego_boundary_loss: 0,
      delusional_affinity: 0,
    };
    return {
      totalInternalizing: Number(diagnostic.total_internalizing_score) || 0,
      riskLevel: diagnostic.internalizing_risk_level || "NORMAL",
      egoBoundaryLoss: Number(sch.ego_boundary_loss) || 0,
      looseAssociation: Number(sch.loose_association) || 0,
    };
  }

  // neurodevelopmental_matrix / unknown — best-effort proxies
  const spectrum = (doc.spectrum_mapping || {}) as Record<string, number>;
  const frag =
    Number(spectrum.cognitive_fragmentation) ||
    Number(doc.cognitive_disorganization_score) ||
    0;
  const total =
    Number(doc.total_internalizing_score) ||
    Number((doc.internalizing_core as { total_internalizing_score?: number } | undefined)?.total_internalizing_score) ||
    frag;
  const risk =
    (doc.internalizing_risk_level as string) ||
    (total > 70 ? "HIGH_ALERT" : total > 40 ? "MONITOR" : "NORMAL");

  return {
    totalInternalizing: total,
    riskLevel: risk,
    egoBoundaryLoss: frag,
    looseAssociation: frag,
  };
}

export function extractKeyEmotionWord(
  userChatMessage: string,
  behaviorLog?: unknown,
  diagnostic?: BlueprintDiagnostic
): string {
  const text = String(userChatMessage || "");
  const metrics = parseBlueprintMetrics(diagnostic);
  const log = (behaviorLog || {}) as Record<string, unknown>;
  const hesitation = Number(log.hesitation_index) || 0;
  const backspaces = Number(log.backspace_count) || 0;

  if (UNCONSCIOUS_RE.test(text) || metrics.looseAssociation > 55 || metrics.egoBoundaryLoss > 55) {
    return "무의식 조각";
  }
  if (AUTONOMIC_RE.test(text) || hesitation > 0.45 || backspaces >= 8) {
    return "자율신경 과활성";
  }
  if (DEPRESSIVE_RE.test(text) || metrics.totalInternalizing > 55) {
    return "우울 궤적";
  }
  // Fallback by dominant clinical signal
  if (metrics.egoBoundaryLoss >= metrics.totalInternalizing) return "무의식 조각";
  if (hesitation > 0.25) return "자율신경 과활성";
  return "우울 궤적";
}

function ensureCenter(nodes: NetworkNode[]): NetworkNode[] {
  if (nodes.some((n) => n.id === CENTER_ID)) return nodes;
  return [
    {
      id: CENTER_ID,
      label: "self",
      val: 20,
      color: "#f8fafc",
      x: 0,
      y: 0,
      z: 0,
    },
    ...nodes,
  ];
}

function capHistory(graph: BlueprintGraph, maxNodes: number = MAX_HISTORY): BlueprintGraph {
  const center = graph.nodes.find((n) => n.id === CENTER_ID);
  const others = graph.nodes.filter((n) => n.id !== CENTER_ID);
  if (others.length <= maxNodes) {
    return { nodes: ensureCenter(graph.nodes), links: graph.links };
  }
  const kept = others.slice(-maxNodes);
  const keepIds = new Set(kept.map((n) => n.id));
  keepIds.add(CENTER_ID);
  const links = graph.links.filter(
    (l) => keepIds.has(String(l.source)) && keepIds.has(String(l.target))
  );
  return {
    nodes: ensureCenter(center ? [center, ...kept] : kept),
    links,
  };
}

export function buildBlueprintNode(
  userChatMessage: string,
  behaviorLog: unknown,
  diagnostic: BlueprintDiagnostic,
  seq: number
): { node: NetworkNode; link: NetworkLink; label: string } {
  const metrics = parseBlueprintMetrics(diagnostic);
  const label = extractKeyEmotionWord(userChatMessage, behaviorLog, diagnostic);
  const val = metrics.totalInternalizing > 70 ? 15 : 8;
  const color = metrics.riskLevel === "HIGH_ALERT" ? "#ff3333" : "#10b981";
  const linkColor = metrics.egoBoundaryLoss > 50 ? "#a855f7" : "#06b6d4";
  const dashed = metrics.looseAssociation > 60;
  const id = `emo_${seq}_${Date.now().toString(36)}`;
  const angle = (seq % 12) * ((Math.PI * 2) / 12);
  const radius = 2.2 + (seq % 5) * 0.35;

  return {
    label,
    node: {
      id,
      label,
      val,
      color,
      x: Math.cos(angle) * radius,
      y: (seq % 3) - 1,
      z: Math.sin(angle) * radius,
    },
    link: {
      source: CENTER_ID,
      target: id,
      color: linkColor,
      dashed,
    },
  };
}

function initialGraph(): BlueprintGraph {
  return {
    nodes: ensureCenter([]),
    links: [],
  };
}

/**
 * React hook: call `ingest(message, diagnostic, behaviorLog?)` after each user turn.
 */
export function use3DBlueprintBuilder(
  _userChatMessage?: string,
  _behaviorLog?: unknown,
  _diagnostic?: BlueprintDiagnostic
) {
  const [graph, setGraph] = useState<BlueprintGraph>(initialGraph);
  const [lastLabel, setLastLabel] = useState<string>("");
  const [lastDashed, setLastDashed] = useState<boolean>(false);
  const seqRef = useRef(0);

  const ingest = useCallback(
    (message: string, diagnostic?: BlueprintDiagnostic, behaviorLog?: unknown) => {
      const built = buildBlueprintNode(message, behaviorLog, diagnostic, seqRef.current++);
      setLastLabel(built.label);
      setLastDashed(built.link.dashed);
      setGraph((prev) =>
        capHistory({
          nodes: [...ensureCenter(prev.nodes), built.node],
          links: [...prev.links, built.link],
        })
      );
      return built;
    },
    []
  );

  const reset = useCallback(() => {
    seqRef.current = 0;
    setLastLabel("");
    setLastDashed(false);
    setGraph(initialGraph());
  }, []);

  return {
    graph,
    nodes: graph.nodes,
    links: graph.links,
    lastLabel,
    lastDashed,
    ingest,
    reset,
    getGraph: () => graph,
  };
}

export default use3DBlueprintBuilder;
