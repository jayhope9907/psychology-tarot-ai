# 마음쉼터 (Maum Shelter) — Invention Disclosure Pack

**문서 버전:** 1.0  
**작성 목적:** 국내 특허 출원·변리사 상담·기술이전·정부 R&D 기술성 평가용 발명 개시  
**서비스 성격:** AI 기반 **마음 웰니스·자기성찰·학회/수련 교육 보조** (비의료·비진단)

> **비청구(Non-claims):** 본 발명은 정신과 진단, 질병 치료, 약물 처방, 의료기기 성능을 주장하지 않습니다.  
> 실제 특허 청구항은 변리사와 함께 prior art 조사 후 확정해야 합니다.

---

## 1. 기술 분야

디지털 정신건강 **웰니스·교육** 소프트웨어; 멀티모달 대화형 AI; 학회 B2B 라이선싱; 종단 자기모니터링 UX.

## 2. 해결하려는 문제

1. 일반 LLM 챗봇은 **학회/수련 유형별 허용 도구·법적 프레이밍**을 구분하지 못함.  
2. 다수 스크리닝·투영 표현 도구를 넣으면 **피로·과검**이 발생.  
3. 수련기관은 발급 직후 **교육용 사례·종단 데이터**가 없어 온보딩이 느림.  
4. 타로·사진·픽토 등 **상징 입력**을 의료화하지 않고 구조화 대화에 연결하기 어려움.

## 3. 핵심 발명 후보 (시스템·방법)

| ID | 제목 | 신규성 요지 |
|----|------|-------------|
| **INV-01** | 피로·단계 인식형 다도구 상담 오케스트레이터 | 세션 피로·상담 단계·도구 이력에 따라 검사 주입 vs 대화 vs 워밍업을 선택 |
| **INV-02** | 학회·수련 라이선스 권한 기반 AI 에이전트 라우팅 | discipline entitlements → 허용 검사·기능 플래그 → 에이전트 지시문/도구 집합 |
| **INV-03** | 라이선스 발급 시 종단 데모 사례 백데이팅 시드 | provision 시 데모 사례·psych timeline 백필로 수련 샌드박스 즉시 구성 |
| **INV-04** | 상징 모달리티↔구조화 웰니스 대화 브리지 | 타로·픽토·사진검색/비전을 비진단 제약 하에 대화 스트림에 결합 |
| **INV-05** | 투영 표현 배터리 + 종단 psych timeline 파이프라인 | 그림·이야기 표현과 종단 이벤트 저장을 라이선스 필터와 통합 |

### 실시예 (요약)

1. 사용자 메시지 수신 → 위기 키워드 검사 → (해당 시) 전문기관 핸드오프.  
2. 오케스트레이터가 피로·단계·권한을 평가해 action 결정.  
3. 라이선스 entitlements로 카탈로그·에이전트 필터.  
4. 멀티모달 입력이 있으면 비진단 시스템 프롬프트 블록 주입 후 응답 스트림.  
5. 종단 이벤트는 연구 export 시 비식별 집계만 기본 제공.

## 4. 선행기술과의 차별 (초안)

- 단순 LLM 챗봇 / 단일 PHQ 앱: **학회 렌즈·피로 게이트·수련 시드** 없음.  
- 의료 EMR·진단 AI: 본 시스템은 **의도적으로 비진단**이며 위기 연계·교육용.  
- 타로 앱 단독: **상담 단계·검사 오케스트레이션·B2B 라이선스**와 결합되지 않음.

## 5. 구현 모듈 (코드 맵)

- `app/services/orchestrator.py`, `fatigue_manager.py`, `counseling_phase.py`  
- `app/services/association_licensing.py`, `association_agent.py`, `license_store.py`, `license_case_seed.py`  
- `app/services/tarot_bridge.py`, `image_search.py`, `chat_stream.py`  
- `app/assessments/projective_battery.py`, `app/services/psych_timeline.py`  
- `app/services/research_export.py` (연구·지원 KPI)

## 6. 변리사 전달 체크리스트

- [ ] prior art 검색 (국내·PCT 키워드: counseling orchestrator, digital wellness, license entitlement AI)  
- [ ] 청구항: 시스템 / 방법 / 컴퓨터 판독 매체 (효능·진단 표현 배제)  
- [ ] 도면: 시퀀스 다이어그램(오케스트레이터), 라이선스→에이전트 플로우, 시드 백필  
- [ ] 발명자·출원인·직무발명 확인  
- [ ] 공개일(GitHub·데모 URL)과 출원 전략(국내 우선 → PCT)

## 7. 공개·데모

- Association License: `/associations`  
- 혁신·지원 허브: `/innovation`  
- API: `/api/v1/research/inventions`, `/api/v1/research/grant-kpis`
