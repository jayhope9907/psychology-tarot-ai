/**
 * MindNetwork3D — 직면 거울 + Future Projection Morphing 참조 구현.
 *
 * 채팅 UI는 static/js/mind-network-3d.js (vanilla)가 실사용합니다.
 *
 * Phases (Now You See Me style):
 *   mirror     — DSM5/Integrated 고착·파편 노드를 거울 프레임 안에 렌더
 *   shatter    — 유리 glow cracks + glass particle burst
 *   freeze     — 파편 공중 정지
 *   morph      — CHC 5축 emerald/gold 건강 신경망으로 lerp 재조립
 *   flythrough — 어두운 거울을 뚫고 미래 도면으로 camera fly
 *   future     — 완성된 미래 자아 신경망
 *
 * Trigger: scene.playFutureProjection(diagnostic) | onConfrontationComplete()
 */
import React, { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { DSM5IntegratedDiagnostic } from "../types/DSM5IntegratedDiagnostic";
import {
  CognitiveProfile,
  IntegratedDiagnosticModel,
} from "../types/IntegratedDiagnosticModel";

export type MindNetworkDiagnostic = DSM5IntegratedDiagnostic | IntegratedDiagnosticModel;

export type FutureProjectionPhase =
  | "mirror"
  | "shatter"
  | "freeze"
  | "morph"
  | "flythrough"
  | "future";

export const CHC_NODE_DEFS = [
  { id: "chc_g", label: "g · 전체", key: "g_factor" as const, color: "#fbbf24" },
  { id: "chc_gc", label: "Gc · 언어", key: "crystallized_gc" as const, color: "#34d399" },
  { id: "chc_gf", label: "Gf · 유동", key: "fluid_gf" as const, color: "#10b981" },
  { id: "chc_gwm", label: "Gwm · 작업기억", key: "working_memory_gwm" as const, color: "#059669" },
  { id: "chc_gs", label: "Gs · 처리속도", key: "processing_speed_gs" as const, color: "#eab308" },
  { id: "chc_gv", label: "Gv · 시공간", key: "visual_processing_gv" as const, color: "#f59e0b" },
] as const;

interface MindNetwork3DProps {
  diagnosticData: MindNetworkDiagnostic;
  /** When true, plays Future Projection Morphing cinematic */
  confrontationComplete?: boolean;
  onPhaseChange?: (phase: FutureProjectionPhase) => void;
}

function isIntegratedModel(data: MindNetworkDiagnostic): data is IntegratedDiagnosticModel {
  return Boolean(
    data &&
      typeof data === "object" &&
      "clinicalProfile" in data &&
      (data as IntegratedDiagnosticModel).clinicalProfile
  );
}

export function parseNetworkMetrics(data: MindNetworkDiagnostic): {
  asdRigidity: number;
  schFragmentation: number;
} {
  const clamp01 = (n: number) => Math.min(1, Math.max(0, n));

  if (isIntegratedModel(data)) {
    const cp = data.clinicalProfile || {
      schizophrenia_index: 0,
      asd_stimming_index: 0,
      depression_index: 0,
    };
    const tm = data.threeRenderMetrics || { backbone_tension: 50, cluster_density: 0 };
    const asdRaw = Number(cp.asd_stimming_index);
    const asdRigidity = clamp01(
      Number.isFinite(asdRaw) && asdRaw > 0 ? asdRaw / 100 : (Number(tm.cluster_density) || 0) / 100
    );
    const schFragmentation = clamp01((Number(cp.schizophrenia_index) || 0) / 100);
    return { asdRigidity, schFragmentation };
  }

  const dims = data.dimensions || ({} as DSM5IntegratedDiagnostic["dimensions"]);
  const sch = dims.schizophrenia_spectrum || {
    loose_association: 0,
    thought_blocking: 0,
    ego_boundary_loss: 0,
    delusional_affinity: 0,
  };
  return {
    asdRigidity: clamp01((Number(dims.obsessive_compulsive) || 0) / 100),
    schFragmentation: clamp01((Number(sch.ego_boundary_loss) || 0) / 100),
  };
}

export function parseCognitiveProfile(data: MindNetworkDiagnostic): CognitiveProfile {
  if (isIntegratedModel(data) && data.cognitiveProfile) return data.cognitiveProfile;
  const total = Number((data as DSM5IntegratedDiagnostic).total_internalizing_score) || 50;
  const base = Math.max(70, 130 - total * 0.45);
  return {
    g_factor: base,
    crystallized_gc: base - 2,
    fluid_gf: base - 4,
    working_memory_gwm: base - 6,
    processing_speed_gs: base - 5,
    visual_processing_gv: base - 3,
  };
}

/** CHC layout targets for Future Morphing Engine */
export function buildChcFutureLayout(cognitive: CognitiveProfile) {
  const nodes = [
    {
      id: CHC_NODE_DEFS[0].id,
      label: CHC_NODE_DEFS[0].label,
      color: CHC_NODE_DEFS[0].color,
      x: 0,
      y: 0,
      z: -3.2,
      score: Number(cognitive.g_factor) || 100,
    },
  ];
  for (let i = 1; i < CHC_NODE_DEFS.length; i++) {
    const def = CHC_NODE_DEFS[i];
    const ang = ((i - 1) / (CHC_NODE_DEFS.length - 1)) * Math.PI * 2 - Math.PI / 2;
    const score = Number(cognitive[def.key]) || 100;
    const radius = 1.55 + (score / 150) * 0.55;
    nodes.push({
      id: def.id,
      label: def.label,
      color: def.color,
      x: Math.cos(ang) * radius,
      y: Math.sin(ang) * radius * 0.85,
      z: -3.2 + Math.sin(ang * 2) * 0.35,
      score,
    });
  }
  return nodes;
}

const PARTICLE_COUNT = 200;

const MirrorFrame: React.FC = () => (
  <group position={[0, 0, -0.35]}>
    <mesh>
      <boxGeometry args={[3.4, 4.6, 0.12]} />
      <meshStandardMaterial color="#c4a574" metalness={0.75} roughness={0.28} />
    </mesh>
    <mesh position={[0, 0, 0.08]}>
      <planeGeometry args={[2.85, 4.0]} />
      <meshStandardMaterial
        color="#7eb6ff"
        transparent
        opacity={0.32}
        metalness={0.2}
        roughness={0.12}
        side={THREE.DoubleSide}
      />
    </mesh>
  </group>
);

const NeuralNetworkGraph: React.FC<{
  data: MindNetworkDiagnostic;
  phase: FutureProjectionPhase;
}> = ({ data, phase }) => {
  const pointsRef = useRef<THREE.Points>(null);
  const { asdRigidity, schFragmentation } = parseNetworkMetrics(data);
  const internalScore =
    (data as IntegratedDiagnosticModel).internalizing_core?.total_internalizing_score ??
    (data as DSM5IntegratedDiagnostic).total_internalizing_score ??
    0;
  const internalizingPressure = Math.min(1, Math.max(0, Number(internalScore) / 100));
  const amp = 1.0 + internalizingPressure * 0.5;
  const futureLayout = useMemo(
    () => buildChcFutureLayout(parseCognitiveProfile(data)),
    [data]
  );

  useFrame((state) => {
    if (!pointsRef.current || phase !== "mirror") return;
    const time = state.clock.getElapsedTime();
    const geometry = pointsRef.current.geometry as THREE.BufferGeometry;
    const positions = geometry.attributes.position.array as Float32Array;

    for (let i = 0; i < positions.length; i += 3) {
      if (schFragmentation > 0.6) {
        positions[i] += Math.sin(time + i) * 0.05 * schFragmentation * amp;
        positions[i + 1] += Math.cos(time + i) * 0.05 * schFragmentation * amp;
        positions[i + 2] += Math.sin(time * 0.5 + i) * 0.05 * schFragmentation * amp;
      } else if (asdRigidity > 0.6) {
        positions[i] = THREE.MathUtils.lerp(positions[i], Math.sin(i) * 0.5, 0.02 * amp);
        positions[i + 1] = THREE.MathUtils.lerp(positions[i + 1], Math.cos(i) * 0.5, 0.02 * amp);
      } else {
        positions[i + 1] += Math.sin(time + positions[i]) * 0.005 * amp;
      }
    }
    geometry.attributes.position.needsUpdate = true;
  });

  const positions = useMemo(() => {
    const pos = new Float32Array(PARTICLE_COUNT * 3);
    for (let i = 0; i < PARTICLE_COUNT * 3; i += 3) {
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = 2.2 * Math.cbrt(Math.random());
      pos[i] = r * Math.sin(phi) * Math.cos(theta);
      pos[i + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i + 2] = r * Math.cos(phi) * 0.35 - 0.55;
    }
    return pos;
  }, []);

  const networkColor =
    internalizingPressure > 0.75
      ? "#ff3333"
      : schFragmentation > 0.6
        ? "#a855f7"
        : asdRigidity > 0.6
          ? "#06b6d4"
          : "#10b981";

  return (
    <group>
      {phase === "mirror" && <MirrorFrame />}
      {phase === "mirror" && (
        <points ref={pointsRef}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              args={[positions, 3]}
              count={PARTICLE_COUNT}
              array={positions}
              itemSize={3}
            />
          </bufferGeometry>
          <pointsMaterial size={0.12} color={networkColor} sizeAttenuation transparent opacity={0.8} />
        </points>
      )}
      {(phase === "morph" || phase === "flythrough" || phase === "future") &&
        futureLayout.map((n) => (
          <mesh key={n.id} position={[n.x, n.y, n.z]}>
            <sphereGeometry args={[n.id === "chc_g" ? 0.38 : 0.16, 24, 24]} />
            <meshStandardMaterial
              color={n.color}
              emissive={n.color}
              emissiveIntensity={0.5}
              metalness={0.55}
              roughness={0.18}
            />
          </mesh>
        ))}
    </group>
  );
};

export const MindNetwork3D: React.FC<MindNetwork3DProps> = ({
  diagnosticData,
  confrontationComplete = false,
  onPhaseChange,
}) => {
  const [phase, setPhase] = useState<FutureProjectionPhase>("mirror");

  useEffect(() => {
    if (!confrontationComplete) {
      setPhase("mirror");
      onPhaseChange?.("mirror");
      return;
    }
    const steps: { phase: FutureProjectionPhase; ms: number }[] = [
      { phase: "shatter", ms: 0 },
      { phase: "freeze", ms: 850 },
      { phase: "morph", ms: 1600 },
      { phase: "flythrough", ms: 3500 },
      { phase: "future", ms: 5600 },
    ];
    const timers = steps.map(({ phase: p, ms }) =>
      window.setTimeout(() => {
        setPhase(p);
        onPhaseChange?.(p);
      }, ms)
    );
    return () => timers.forEach(clearTimeout);
  }, [confrontationComplete, onPhaseChange]);

  return (
    <div
      style={{
        width: "100%",
        height: "500px",
        backgroundColor: phase === "future" || phase === "flythrough" ? "#071510" : "#0b0f19",
        borderRadius: "12px",
        overflow: "hidden",
      }}
      data-phase={phase}
      aria-label="직면 거울 Future Projection"
    >
      <Canvas camera={{ position: [0, 1.2, 8], fov: 55 }}>
        <ambientLight intensity={0.55} />
        <directionalLight position={[4, 8, 6]} intensity={0.85} />
        <pointLight position={[0, 0, -2]} intensity={phase === "mirror" ? 0 : 2.4} color="#34d399" />
        <NeuralNetworkGraph data={diagnosticData} phase={phase} />
        <OrbitControls enableZoom enablePan={false} enabled={phase === "mirror" || phase === "future"} />
      </Canvas>
    </div>
  );
};

export default MindNetwork3D;
