# 제품선 (Product Lines)

| 제품 | 대상 | 상태 | 진입 |
|------|------|------|------|
| **유저용** | 일반 사용자 | live | `/`, `/home`, `/chat`, `/tarot`, `/clinical` |
| **라이선스** | 학회·수련 기관 | live | `/associations` → `/theories`, `/expressive`, 임상의 3D 도면(`/chat`), 연령군 익스포트 API |
| **장애인용** | AAC·접근성 | 보관(별도 제품) | `/disability`, `/disability/picto` |

- API 매니페스트: `GET /api/v1/product/surfaces`
- 라이선스 플래그: `emotional_spectrum`, `mind_network_3d`, `integrated_diagnostic`, `age_cohort_export`, `stealth_unconscious_engine`, `b2b_export`
- 11종 소품 무의식 매핑(스텔스 엔진): 게임 UI `/stealth-props` → `POST /api/v1/users/{user_id}/stealth-unconscious/ingest` — 고유 프롭 8개 이상 시 각성(final), 결과는 `integrated_diagnostic_model`로 임상의 3D 미래 도면에 병합
- 장애인용 자산: `docs/disability-product.md`
- 유저 앱에서 숨김: `/picto`(안내), `/theories`, `/expressive`, 통합앱 picto 탭
