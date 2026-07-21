/**
 * MindNetwork3D — DSM5 / IntegratedDiagnosticModel 기반 신경망 파티클 참조 구현.
 *
 * 채팅 UI에서는 static/js/mind-network-3d.js (vanilla)가 실사용됩니다.
 * 이 파일은 React/Three 타입 계약을 고정하기 위한 참조 구현입니다.
 */
import React, { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { DSM5IntegratedDiagnostic } from "../types/DSM5IntegratedDiagnostic";
import { IntegratedDiagnosticModel } from "../types/IntegratedDiagnosticModel";

export type MindNetworkDiagnostic = DSM5IntegratedDiagnostic | IntegratedDiagnosticModel;

interface MindNetwork3DProps {
  diagnosticData: MindNetworkDiagnostic;
}

function isIntegratedModel(data: MindNetworkDiagnostic): data is IntegratedDiagnosticModel {
  return Boolean(
    data &&
      typeof data === "object" &&
      "clinicalProfile" in data &&
      (data as IntegratedDiagnosticModel).clinicalProfile
  );
}

/** ASD 고착도 / SCH 와해도 (0..1) — 두 계약 모두 지원 */
export function parseNetworkMetrics(data: MindNetworkDiagnostic): {
  asdRigidity: number;
  schFragmentation: number;
} {
  const clamp01 = (n: number) => Math.min(1, Math.max(0, n));

  if (isIntegratedModel(data)) {
    const cp = data.clinicalProfile || { schizophrenia_index: 0, asd_stimming_index: 0, depression_index: 0 };
    const tm = data.threeRenderMetrics || { backbone_tension: 50, cluster_density: 0 };
    const asdRaw = Number(cp.asd_stimming_index);
    const asdRigidity = clamp01(
      Number.isFinite(asdRaw) && asdRaw > 0
        ? asdRaw / 100
        : (Number(tm.cluster_density) || 0) / 100
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

const PARTICLE_COUNT = 200;

const NeuralNetworkGraph: React.FC<{ data: MindNetworkDiagnostic }> = ({ data }) => {
  const pointsRef = useRef<THREE.Points>(null);
  const { asdRigidity, schFragmentation } = parseNetworkMetrics(data);

  // 옵시디언 그래프처럼 프레임마다 노드들의 유기적 움직임 연산
  useFrame((state) => {
    if (!pointsRef.current) return;

    const time = state.clock.getElapsedTime();
    const geometry = pointsRef.current.geometry as THREE.BufferGeometry;
    const positions = geometry.attributes.position.array as Float32Array;

    for (let i = 0; i < positions.length; i += 3) {
      if (schFragmentation > 0.6) {
        // [조현병 스펙트럼]: 노드가 중심에서 흩어져 파편화
        positions[i] += Math.sin(time + i) * 0.05 * schFragmentation;
        positions[i + 1] += Math.cos(time + i) * 0.05 * schFragmentation;
        positions[i + 2] += Math.sin(time * 0.5 + i) * 0.05 * schFragmentation;
      } else if (asdRigidity > 0.6) {
        // [자폐 스펙트럼]: 특정 축(고정점)으로 노드가 압축
        positions[i] = THREE.MathUtils.lerp(positions[i], Math.sin(i) * 0.5, 0.02);
        positions[i + 1] = THREE.MathUtils.lerp(positions[i + 1], Math.cos(i) * 0.5, 0.02);
      } else {
        // 안정 상태: 부드러운 신경망 파동
        positions[i + 1] += Math.sin(time + positions[i]) * 0.005;
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
      const r = 3.0 * Math.cbrt(Math.random());

      pos[i] = r * Math.sin(phi) * Math.cos(theta);
      pos[i + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i + 2] = r * Math.cos(phi);
    }
    return pos;
  }, []);

  const getNetworkColor = (): string => {
    if (schFragmentation > 0.6) return "#a855f7"; // 파편화 보라
    if (asdRigidity > 0.6) return "#06b6d4"; // 고착 시안
    return "#10b981"; // 안정 에메랄드
  };

  return (
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
      <pointsMaterial
        size={0.12}
        color={getNetworkColor()}
        sizeAttenuation={true}
        transparent
        opacity={0.8}
      />
    </points>
  );
};

export const MindNetwork3D: React.FC<MindNetwork3DProps> = ({ diagnosticData }) => {
  return (
    <div
      style={{
        width: "100%",
        height: "500px",
        backgroundColor: "#0b0f19",
        borderRadius: "12px",
        overflow: "hidden",
      }}
    >
      <Canvas camera={{ position: [0, 0, 7], fov: 60 }}>
        <NeuralNetworkGraph data={diagnosticData} />
        <OrbitControls enableZoom={true} />
      </Canvas>
    </div>
  );
};
