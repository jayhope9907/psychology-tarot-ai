/**
 * use3DBlueprintBuilder — React reference for real-time emotion-noun graph.
 *
 * Chat UI uses static/js/blueprint-builder.js (vanilla). This file fixes the
 * TypeScript contract: multi-noun nodes → center_self edges, SCH dashed,
 * ASD dense hubs.
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
  kind?: "center" | "emotion";
  fixation?: boolean;
  x?: number;
  y?: number;
  z?: number;
}

export interface NetworkLink {
  source: string;
  target: string;
  color: string;
  dashed: boolean;
  dense?: boolean;
  strength?: number;
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
  schizophreniaIndex: number;
  asdStimmingIndex: number;
}

export const CENTER_ID = "center_self";
const MAX_HISTORY = 40;
const MAX_NOUNS_PER_TURN = 4;

const DEPRESSIVE_RE =
  /우울|가라앉|무기력|공허|슬프|희망\s*없|눈물|depress|sad|hopeless|empty/i;
const AUTONOMIC_RE =
  /불안|초조|긴장|두근|공황|숨\s*막|자율신경|과활성|심박|anxiety|panic|nervous|jitter/i;
const UNCONSCIOUS_RE =
  /꿈|무의식|환상|해리|와해|파편|연상|망상|이상한\s*생각|fragment|dream|dissoc|delusion/i;

export const EMOTION_NOUNS = [
  "우울", "불안", "공포", "분노", "죄책", "수치", "수치심", "외로움", "고독", "공허",
  "무기력", "절망", "희망", "기쁨", "안도", "긴장", "초조", "공황", "자책", "혐오",
  "질투", "슬픔", "고립", "압박", "스트레스", "피로", "지침", "혼란", "와해", "해리",
  "망상", "환청", "집착", "반복", "루틴", "강박", "자존감", "애착", "거절", "배신",
  "불신", "수치감", "shame", "guilt", "fear", "anger", "sadness", "anxiety", "panic",
  "loneliness", "emptiness", "stress", "fatigue", "obsession", "attachment", "rejection",
];

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
    const sch = Number(diagnostic.clinicalProfile?.schizophrenia_index) || 0;
    const asd =
      Number(diagnostic.clinicalProfile?.asd_stimming_index) ||
      Number(diagnostic.threeRenderMetrics?.cluster_density) ||
      0;
    return {
      totalInternalizing: total,
      riskLevel: risk,
      egoBoundaryLoss: sch,
      looseAssociation: sch,
      schizophreniaIndex: sch,
      asdStimmingIndex: asd,
    };
  }

  if (isDsm5(diagnostic)) {
    const sch = diagnostic.dimensions?.schizophrenia_spectrum || {
      loose_association: 0,
      thought_blocking: 0,
      ego_boundary_loss: 0,
      delusional_affinity: 0,
    };
    const loose = Number(sch.loose_association) || 0;
    const ego = Number(sch.ego_boundary_loss) || 0;
    return {
      totalInternalizing: Number(diagnostic.total_internalizing_score) || 0,
      riskLevel: diagnostic.internalizing_risk_level || "NORMAL",
      egoBoundaryLoss: ego,
      looseAssociation: loose,
      schizophreniaIndex: (loose + ego) / 2,
      asdStimmingIndex: Number(diagnostic.dimensions?.obsessive_compulsive) || 0,
    };
  }

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
    schizophreniaIndex: frag,
    asdStimmingIndex: Number(spectrum.asd_rigidity) || 0,
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
  if (metrics.egoBoundaryLoss >= metrics.totalInternalizing) return "무의식 조각";
  if (hesitation > 0.25) return "자율신경 과활성";
  return "우울 궤적";
}

export function extractEmotionNouns(
  userChatMessage: string,
  behaviorLog?: unknown,
  diagnostic?: BlueprintDiagnostic
): string[] {
  const text = String(userChatMessage || "");
  const found: string[] = [];
  const seen = new Set<string>();
  const lower = text.toLowerCase();
  for (const noun of EMOTION_NOUNS) {
    const key = noun.toLowerCase();
    if (seen.has(key)) continue;
    if (lower.includes(key) || text.includes(noun)) {
      seen.add(key);
      found.push(noun);
      if (found.length >= MAX_NOUNS_PER_TURN) break;
    }
  }
  if (!found.length) found.push(extractKeyEmotionWord(userChatMessage, behaviorLog, diagnostic));
  return found;
}

function ensureCenter(nodes: NetworkNode[]): NetworkNode[] {
  if (nodes.some((n) => n.id === CENTER_ID)) return nodes;
  return [
    {
      id: CENTER_ID,
      label: "self",
      val: 20,
      color: "#f8fafc",
      kind: "center",
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

function buildDenseHubLinks(
  nodes: NetworkNode[],
  hubId: string,
  asdIndex: number
): NetworkLink[] {
  if (!(asdIndex > 60)) return [];
  const others = nodes.filter((n) => n.id !== CENTER_ID && n.id !== hubId);
  const maxExtra = Math.min(8, Math.max(2, Math.floor((asdIndex - 60) / 5)));
  return others.slice(0, maxExtra).map((n) => ({
    source: hubId,
    target: n.id,
    color: "#06b6d4",
    dashed: false,
    dense: true,
    strength: 0.35 + asdIndex / 200,
  }));
}

export function buildBlueprintTurn(
  userChatMessage: string,
  behaviorLog: unknown,
  diagnostic: BlueprintDiagnostic,
  seq: number
): { nodes: NetworkNode[]; links: NetworkLink[]; labels: string[]; dashed: boolean } {
  const metrics = parseBlueprintMetrics(diagnostic);
  const nouns = extractEmotionNouns(userChatMessage, behaviorLog, diagnostic);
  const val = metrics.totalInternalizing > 70 ? 15 : 8;
  const color = metrics.riskLevel === "HIGH_ALERT" ? "#ff3333" : "#10b981";
  const schHigh = metrics.schizophreniaIndex > 60 || metrics.looseAssociation > 60;
  const linkColor =
    metrics.egoBoundaryLoss > 50 || metrics.schizophreniaIndex > 50 ? "#a855f7" : "#06b6d4";
  const nodes: NetworkNode[] = [];
  const links: NetworkLink[] = [];

  nouns.forEach((noun, i) => {
    const id = `emo_${seq + i}_${Date.now().toString(36)}_${i}`;
    const angle = ((seq + i) % 12) * ((Math.PI * 2) / 12) + i * 0.15;
    const radius = 2.2 + ((seq + i) % 5) * 0.35;
    const fixation = /집착|반복|루틴|강박|obsession/i.test(noun);
    nodes.push({
      id,
      label: noun,
      val,
      color,
      kind: "emotion",
      fixation,
      x: Math.cos(angle) * radius,
      y: ((seq + i) % 3) - 1,
      z: Math.sin(angle) * radius,
    });
    links.push({
      source: CENTER_ID,
      target: id,
      color: linkColor,
      dashed: schHigh,
    });
  });

  return { nodes, links, labels: nouns, dashed: schHigh };
}

function initialGraph(): BlueprintGraph {
  return { nodes: ensureCenter([]), links: [] };
}

export function use3DBlueprintBuilder() {
  const [graph, setGraph] = useState<BlueprintGraph>(initialGraph);
  const [lastLabel, setLastLabel] = useState("");
  const [lastDashed, setLastDashed] = useState(false);
  const seqRef = useRef(0);

  const ingest = useCallback(
    (message: string, diagnostic?: BlueprintDiagnostic, behaviorLog?: unknown) => {
      const built = buildBlueprintTurn(message, behaviorLog, diagnostic, seqRef.current);
      seqRef.current += built.nodes.length;
      setLastLabel(built.labels[0] || "");
      setLastDashed(built.dashed);
      setGraph((prev) => {
        let next = capHistory({
          nodes: [...ensureCenter(prev.nodes), ...built.nodes],
          links: [...prev.links, ...built.links],
        });
        const metrics = parseBlueprintMetrics(diagnostic);
        if (metrics.asdStimmingIndex > 60) {
          const hub =
            next.nodes.find((n) => n.fixation) ||
            next.nodes.filter((n) => n.id !== CENTER_ID).slice(-1)[0];
          if (hub) {
            const extras = buildDenseHubLinks(next.nodes, hub.id, metrics.asdStimmingIndex);
            const existing = new Set(next.links.map((l) => `${l.source}>${l.target}`));
            next = {
              ...next,
              links: [
                ...next.links,
                ...extras.filter((l) => !existing.has(`${l.source}>${l.target}`)),
              ],
            };
          }
        }
        return next;
      });
      return built;
    },
    []
  );

  const applyClinicalEffects = useCallback((diagnostic?: BlueprintDiagnostic) => {
    const metrics = parseBlueprintMetrics(diagnostic);
    const schHigh = metrics.schizophreniaIndex > 60 || metrics.looseAssociation > 60;
    const linkColor =
      metrics.egoBoundaryLoss > 50 || metrics.schizophreniaIndex > 50 ? "#a855f7" : "#06b6d4";
    setLastDashed(schHigh);
    setGraph((prev) => ({
      ...prev,
      links: prev.links.map((l) => {
        if (l.dense) return { ...l, color: "#06b6d4", dashed: false };
        if (String(l.source) === CENTER_ID || String(l.target) === CENTER_ID) {
          return { ...l, dashed: schHigh, color: linkColor };
        }
        return l;
      }),
    }));
  }, []);

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
    applyClinicalEffects,
    reset,
    getGraph: () => graph,
  };
}

export default use3DBlueprintBuilder;
