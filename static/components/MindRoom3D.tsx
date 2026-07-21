/**
 * MindRoom3D — DSM5IntegratedDiagnostic 기반 3D "마음의 방" 참조 구현.
 *
 * 채팅 UI에서는 static/js/mind-room-3d.js (vanilla)가 실사용됩니다.
 * 이 파일은 React/Three 타입 계약을 고정하기 위한 참조 구현입니다.
 *
 * Dual-support: DSM5IntegratedDiagnostic | IntegratedDiagnosticModel
 * (neurodevelopmental_matrix wall_texture는 vanilla 런타임에서 처리)
 */
import React, { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { DSM5IntegratedDiagnostic } from "../types/DSM5IntegratedDiagnostic";
import { IntegratedDiagnosticModel } from "../types/IntegratedDiagnosticModel";

export type MindRoomDiagnostic = DSM5IntegratedDiagnostic | IntegratedDiagnosticModel;

interface MindRoom3DProps {
  diagnosticData: MindRoomDiagnostic;
}

function isIntegratedModel(data: MindRoomDiagnostic): data is IntegratedDiagnosticModel {
  return Boolean(
    data &&
      typeof data === "object" &&
      "clinicalProfile" in data &&
      (data as IntegratedDiagnosticModel).clinicalProfile
  );
}

/** Normalize DSM5 + IntegratedDiagnosticModel into room metrics (0..1). */
export function parseRoomMetrics(data: MindRoomDiagnostic): {
  internalizingFactor: number;
  schTotal: number;
} {
  const clamp01 = (n: number) => Math.min(1, Math.max(0, n));

  if (isIntegratedModel(data)) {
    const cp = data.clinicalProfile || {
      schizophrenia_index: 0,
      asd_stimming_index: 0,
      depression_index: 0,
    };
    const coreScore = data.internalizing_core?.total_internalizing_score;
    const rawInternal =
      typeof coreScore === "number" && Number.isFinite(coreScore)
        ? coreScore
        : Number(cp.depression_index) || 0;
    return {
      internalizingFactor: clamp01(rawInternal / 100),
      schTotal: clamp01((Number(cp.schizophrenia_index) || 0) / 100),
    };
  }

  const dims = data.dimensions || ({} as DSM5IntegratedDiagnostic["dimensions"]);
  const sch = dims.schizophrenia_spectrum || {
    loose_association: 0,
    thought_blocking: 0,
    ego_boundary_loss: 0,
    delusional_affinity: 0,
  };
  return {
    internalizingFactor: clamp01((Number(data.total_internalizing_score) || 0) / 100),
    schTotal: clamp01(
      ((Number(sch.loose_association) || 0) + (Number(sch.ego_boundary_loss) || 0)) / 200
    ),
  };
}

// 방의 동적 변화를 담당하는 내부 3D 메시 컴포넌트
const DynamicRoomMesh: React.FC<{ data: MindRoomDiagnostic }> = ({ data }) => {
  const roomRef = useRef<THREE.Mesh>(null);
  const lightRef = useRef<THREE.AmbientLight>(null);

  const { internalizingFactor, schTotal } = parseRoomMetrics(data);

  useFrame((state) => {
    if (roomRef.current) {
      // 1. [내재화 반영] 점수가 높을수록 천장이 낮아지고 공간이 수축됨 (Y축 스케일 다운)
      const targetYScale = 1.0 - internalizingFactor * 0.5; // 최대 50% 수축
      roomRef.current.scale.y = THREE.MathUtils.lerp(roomRef.current.scale.y, targetYScale, 0.05);

      // 2. [조현병 와해성 반영] 점수가 높을수록 방이 기괴하게 회전하거나 뒤틀림
      if (schTotal > 0.5) {
        roomRef.current.rotation.x = Math.sin(state.clock.getElapsedTime()) * (schTotal * 0.1);
        roomRef.current.rotation.z = Math.cos(state.clock.getElapsedTime()) * (schTotal * 0.1);
      } else {
        roomRef.current.rotation.set(0, 0, 0);
      }
    }

    // 3. [우울/공황 반영] 내재화 지수가 높을수록 방안의 조도를 차단하여 어둡게 설정
    if (lightRef.current) {
      const targetIntensity = 1.0 - internalizingFactor * 0.8; // 최대 80% 어두워짐
      lightRef.current.intensity = THREE.MathUtils.lerp(
        lightRef.current.intensity,
        targetIntensity,
        0.05
      );
    }
  });

  // 임상 상태에 따른 컬러 매핑 변환
  const getRoomColor = (): string => {
    if (schTotal > 0.5) return "#4a2c5e"; // 기괴하고 몽환적인 보라색 톤
    if (internalizingFactor >= 0.8) return "#2b2b2b"; // 극도의 우울을 뜻하는 어두운 잿빛
    return "#f4ebd0"; // 안정적인 상태의 따뜻한 샌드 옐로우 톤
  };

  return (
    <>
      <ambientLight ref={lightRef} intensity={0.8} />
      <pointLight
        position={[0, 5, 0]}
        intensity={0.5}
        color={internalizingFactor >= 0.8 ? "#ff3333" : "#ffffff"}
      />

      {/* 내담자의 심리가 투사되는 가상의 3D 큐브 공간 */}
      <mesh ref={roomRef}>
        <boxGeometry args={[10, 8, 10]} />
        <meshStandardMaterial
          color={getRoomColor()}
          side={THREE.BackSide} // 큐브의 '내부' 벽면이 보이도록 설정
          wireframe={schTotal > 0.6} // 조현병 와해성이 극도로 높을 때 프레임이 깨지는 시각 효과
        />
      </mesh>
    </>
  );
};

export const MindRoom3D: React.FC<MindRoom3DProps> = ({ diagnosticData }) => {
  return (
    <div style={{ width: "100%", height: "500px", borderRadius: "12px", overflow: "hidden" }}>
      <Canvas camera={{ position: [0, 0, 8], fov: 60 }}>
        <DynamicRoomMesh data={diagnosticData} />
        {/* 마우스나 터치로 방을 360도 회전하며 둘러볼 수 있는 조작계 */}
        <OrbitControls enableZoom={false} maxPolarAngle={Math.PI / 2} minPolarAngle={Math.PI / 3} />
      </Canvas>
    </div>
  );
};
