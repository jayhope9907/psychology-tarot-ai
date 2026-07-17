/**
 * MindRoom3D — 심리 상태가 투사되는 가상 3D 방 (React Three Fiber 계약 구현).
 *
 * Vanilla 런타임 포트: static/js/mind-room-3d.js (chat.html에서 사용).
 * 이 파일은 React 클라이언트용 참조 구현이며 동일한 시각 규칙을 공유한다:
 *   - 내재화 점수 ↑ → 천장 수축(Y 스케일 최대 50%) + 조도 차단(최대 80%)
 *   - 와해성(schTotal) > 0.5 → 방이 기괴하게 뒤틀리는 회전 왜곡
 *   - schTotal > 0.6 → 와이어프레임(프레임 깨짐) 효과
 */
import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { DSM5IntegratedDiagnostic } from '../types/DSM5IntegratedDiagnostic';

interface MindRoom3DProps {
  diagnosticData: DSM5IntegratedDiagnostic;
}

// 방의 동적 변화를 담당하는 내부 3D 메시 컴포넌트
const DynamicRoomMesh: React.FC<{ data: DSM5IntegratedDiagnostic }> = ({ data }) => {
  const roomRef = useRef<THREE.Mesh>(null);
  const lightRef = useRef<THREE.AmbientLight>(null);

  // 내재화 점수(0-100)를 바탕으로 3D 속성 정규화 연산
  const internalizingFactor = data.total_internalizing_score / 100;
  const schTotal =
    (data.dimensions.schizophrenia_spectrum.loose_association +
      data.dimensions.schizophrenia_spectrum.ego_boundary_loss) /
    200;

  useFrame((state) => {
    if (roomRef.current) {
      // 1. [내재화 반영] 점수가 높을수록 천장이 낮아지고 공간이 수축됨 (Y축 스케일 다운)
      const targetYScale = 1.0 - internalizingFactor * 0.5; // 최대 50% 수축
      roomRef.current.scale.y = THREE.MathUtils.lerp(roomRef.current.scale.y, targetYScale, 0.05);

      // 2. [와해성 반영] 점수가 높을수록 방이 기괴하게 회전하거나 뒤틀림
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
    if (schTotal > 0.5) return '#4a2c5e'; // 기괴하고 몽환적인 보라색 톤
    if (internalizingFactor >= 0.8) return '#2b2b2b'; // 극도의 우울을 뜻하는 어두운 잿빛
    return '#f4ebd0'; // 안정적인 상태의 따뜻한 샌드 옐로우 톤
  };

  return (
    <>
      <ambientLight ref={lightRef} intensity={0.8} />
      <pointLight
        position={[0, 5, 0]}
        intensity={0.5}
        color={internalizingFactor >= 0.8 ? '#ff3333' : '#ffffff'}
      />

      {/* 내담자의 심리가 투사되는 가상의 3D 큐브 공간 */}
      <mesh ref={roomRef}>
        <boxGeometry args={[10, 8, 10]} />
        <meshStandardMaterial
          color={getRoomColor()}
          side={THREE.BackSide} // 큐브의 '내부' 벽면이 보이도록 설정
          wireframe={schTotal > 0.6} // 와해성이 극도로 높을 때 프레임이 깨지는 시각 효과
        />
      </mesh>
    </>
  );
};

export const MindRoom3D: React.FC<MindRoom3DProps> = ({ diagnosticData }) => {
  return (
    <div style={{ width: '100%', height: '500px', borderRadius: '12px', overflow: 'hidden' }}>
      <Canvas camera={{ position: [0, 0, 8], fov: 60 }}>
        <DynamicRoomMesh data={diagnosticData} />
        {/* 마우스나 터치로 방을 360도 회전하며 둘러볼 수 있는 조작계 */}
        <OrbitControls enableZoom={false} maxPolarAngle={Math.PI / 2} minPolarAngle={Math.PI / 3} />
      </Canvas>
    </div>
  );
};
