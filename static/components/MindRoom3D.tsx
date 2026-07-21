/**
 * MindRoom3D — IntegratedDiagnosticModel 기반 3D "마음의 방" 참조 구현.
 *
 * 채팅 UI에서는 static/js/mind-room-3d.js (vanilla)가 실사용됩니다.
 * 이 파일은 React/Three 타입 계약을 고정하기 위한 참조 구현입니다.
 */
import React, { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { IntegratedDiagnosticModel } from "../types/IntegratedDiagnosticModel";

interface MindRoom3DProps {
  diagnosticData: IntegratedDiagnosticModel;
}

const DynamicRoomMesh: React.FC<{ data: IntegratedDiagnosticModel }> = ({ data }) => {
  const roomRef = useRef<THREE.Mesh>(null);
  const lightRef = useRef<THREE.AmbientLight>(null);

  const internalizingFactor =
    (typeof data.internalizing_core?.total_internalizing_score === "number"
      ? data.internalizing_core.total_internalizing_score
      : data.clinicalProfile.depression_index || 0) / 100;
  const schTotal = (data.clinicalProfile.schizophrenia_index || 0) / 100;
  const backboneTension = (data.threeRenderMetrics.backbone_tension || 50) / 100;
  const clusterDensity = (data.threeRenderMetrics.cluster_density || 0) / 100;

  useFrame((state) => {
    if (!roomRef.current) return;

    // 1) backbone_tension이 낮을수록 천장이 더 낮아짐 (최대 50%)
    const targetYScale = 1.0 - (1.0 - backboneTension) * 0.5;
    roomRef.current.scale.y = THREE.MathUtils.lerp(roomRef.current.scale.y, targetYScale, 0.05);

    // 2) cluster_density가 높을수록 좌우/전후가 약간 부풀어 보임
    const targetXZ = 1.0 + clusterDensity * 0.15;
    roomRef.current.scale.x = THREE.MathUtils.lerp(roomRef.current.scale.x, targetXZ, 0.05);
    roomRef.current.scale.z = THREE.MathUtils.lerp(roomRef.current.scale.z, targetXZ, 0.05);

    // 3) 회전 왜곡: sch 신호 + 클러스터 고착이 함께 높을수록 강화
    const warpAmp =
      (schTotal > 0.5 ? schTotal * 0.1 : 0) + (clusterDensity > 0.55 ? clusterDensity * 0.05 : 0);
    if (warpAmp > 0) {
      roomRef.current.rotation.x = Math.sin(state.clock.getElapsedTime()) * warpAmp;
      roomRef.current.rotation.z = Math.cos(state.clock.getElapsedTime()) * warpAmp;
    } else {
      roomRef.current.rotation.set(0, 0, 0);
    }

    // 4) 우울 지수가 높을수록 조도를 낮춤 (최대 80% 차단)
    if (lightRef.current) {
      const targetIntensity = 1.0 - internalizingFactor * 0.8;
      lightRef.current.intensity = THREE.MathUtils.lerp(
        lightRef.current.intensity,
        targetIntensity,
        0.05
      );
    }
  });

  const getRoomColor = (): string => {
    if (schTotal > 0.5) return "#4a2c5e";
    if (internalizingFactor >= 0.8) return "#2b2b2b";
    return "#f4ebd0";
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
          side={THREE.BackSide}
          wireframe={schTotal > 0.6 || clusterDensity > 0.65}
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
        <OrbitControls enableZoom={false} maxPolarAngle={Math.PI / 2} minPolarAngle={Math.PI / 3} />
      </Canvas>
    </div>
  );
};

