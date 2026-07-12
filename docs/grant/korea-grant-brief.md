# 마음쉼터 — 국내 정부지원·R&D 지원 브리프

**버전:** 1.0  
**포지셔닝:** 디지털 **마음 웰니스·교육·학회/수련 보조** SW (의료기기·진단 AI 아님)

---

## 1. 한 줄 요약

학회·수련 유형별로 AI 렌즈·검사·법적 프레이밍을 분리하고,  
피로 인식 오케스트레이션·종단 UX·멀티모달 성찰을 결합한 B2B 교육·웰니스 플랫폼.

## 2. 지원 트랙 정렬 (주장 가능한 범위)

| 트랙 | 정렬 포인트 | 주의 (과대주장 금지) |
|------|-------------|----------------------|
| **중기부 / 창업·스케일업** | B2B Association License, 수련 트랙, SaaS 좌석 | “치료 효과” KPI 사용 금지 |
| **과기정통부 R&D** | 멀티모달·오케스트레이터·종단 파이프라인 | 진단 정확도 지표 금지 |
| **복지부 디지털 정신건강** | 위기 핫라인 연계, 비진단 스크리닝 **교육** | 의료행위·진료 대체 표현 금지 |
| **TIPS형** | 차별화 기술(INV-01~05) + 학회/수련 PoC | 임상 효능을 핵심 성과로 두지 말 것 |

## 3. 기술 차별성 (평가표용)

1. **INV-01** 피로·단계 게이트 오케스트레이터  
2. **INV-02** 학회/수련 entitlements → 에이전트·도구 라우팅  
3. **INV-03** 라이선스 발급 시 데모 사례 타임라인 시드  
4. **INV-04** 타로·픽토·사진 검색/비전 브리지 (비진단)  
5. **INV-05** 투영 표현 + psych timeline  

데모 키: `MSHT-CLINICAL-DEMO-2026`, `MSHT-MHSW-DEMO-2026` 등 (`/associations`)

## 4. 성과지표 (Non-efficacy KPI)

API: `GET /api/v1/research/grant-kpis`

권장 1차 지표:
- 세션 참여·평균 턴 수  
- 위기 핸드오프 **발생률**(내용 비포함)  
- 검사 피로 억제율  
- 학회 좌석 이용률  
- 종단 timeline 커버리지  
- 오프라인 번들 표면(픽토·타로·오프라인 카운슬)

**금지 1차 지표 예:** PHQ 점수 호전율, 진단 concordance, “완치율”

## 5. 연구·IRB형 데이터

- 동의 문서: `GET /api/v1/research/consent`  
- 비식별 export: `POST /api/v1/research/export` (`research_consent: true`)  
- 코드북: `GET /api/v1/research/codebook`  

기본 export에 **대화 전문·사진 원본 미포함**.

## 6. 법·규제 프레이밍

- 서비스 범위: `static/legal.html`, `app/services/legal_compliance.py`  
- 의료법·정신건강복지법상 **비의료** 명시  
- 위기 시 1393 / 119 / 129 / 1577-0199  

## 7. 제출 패키지 체크리스트

- [ ] 본 브리프 + `docs/ip/invention-disclosure.md`  
- [ ] `/innovation` 공개 페이지 스크린샷  
- [ ] Association 라이선스 데모 시나리오  
- [ ] grant-kpis JSON 스냅샷  
- [ ] 개인정보 처리·purge 경로 설명  
- [ ] (선택) 학회·수련기관 MoU 초안  
- [ ] 특허: 변리사 상담·공개일 관리

## 8. 연락·데모

- 혁신 허브: `/innovation`  
- 학회 라이선스: `/associations`  
- 저장소: https://github.com/jayhope9907/psychology-tarot-ai
