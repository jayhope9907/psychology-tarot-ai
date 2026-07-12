# 마음쉼터 (psychology-tarot-ai)

AI 기반 **마음 웰니스·자기성찰·학회/수련 교육 보조** 플랫폼입니다.

> **중요:** 정신과 진료·의료행위·임상심리치료·진단·처방을 제공하지 않습니다.  
> 위기 시 1393 · 119 · 129 · 1577-0199 등 전문 기관을 이용해 주세요.

## 주요 기능

- AI 대화 (상담 단계·피로 인식 오케스트레이션)
- 학회·수련 Association License (상담/심리/정신의학/임상심리 수련/정신보건사회복지 수련)
- 마음 돌보기 · 그림·이야기 표현 · 3D 타로 · 픽토 · 사진 첨부/검색
- 연구용 비식별 export · 정부지원 Non-efficacy KPI (`/innovation`)

## 빠른 실행

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

공개 터널(Windows):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-public.ps1
```

## 문서

| 문서 | 경로 |
|------|------|
| 발명 개시(특허용) | `docs/ip/invention-disclosure.md` |
| 정부지원 브리프 | `docs/grant/korea-grant-brief.md` |
| 이용·법적 안내 | `/legal` |
| 혁신·IP 허브 | `/innovation` |

## API (연구·지원)

- `GET /api/v1/research/consent`
- `GET /api/v1/research/codebook`
- `GET /api/v1/research/inventions`
- `GET /api/v1/research/grant-kpis`
- `POST /api/v1/research/export` — body: `{ "research_consent": true }`

## 데모 라이선스

- `MSHT-COUNSEL-DEMO-2026` · `MSHT-PSYCH-DEMO-2026` · `MSHT-PSYCHIATRY-DEMO-2026`
- `MSHT-CLINICAL-DEMO-2026` · `MSHT-MHSW-DEMO-2026`

## 라이선스·면책

제품 사용은 `/legal` 고지를 따릅니다. 본 README의 기술 설명은 교육·웰니스·R&D 목적입니다.
