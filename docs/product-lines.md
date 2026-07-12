# 제품선 (Product Lines)

| 제품 | 대상 | 상태 | 진입 |
|------|------|------|------|
| **유저용** | 일반 사용자 | live | `/`, `/home`, `/chat`, `/tarot`, `/clinical` |
| **라이선스** | 학회·수련 기관 | live | `/associations` → `/theories`, `/expressive` |
| **장애인용** | AAC·접근성 | 보관(별도 제품) | `/disability`, `/disability/picto` |

- API 매니페스트: `GET /api/v1/product/surfaces`
- 장애인용 자산: `docs/disability-product.md`
- 유저 앱에서 숨김: `/picto`(안내), `/theories`, `/expressive`, 통합앱 picto 탭
