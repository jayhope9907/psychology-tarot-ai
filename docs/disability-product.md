# 장애인용 제품 (분리 보관)

일반 유저용 「마음쉼터」와 **별도 제품**으로 만들 예정입니다.  
아래 자산은 삭제하지 않고 코드베이스에 유지합니다. 유저 앱 탭·바로가기에서는 노출하지 않습니다.

## 제품 표면

| 구분 | 경로 / 파일 |
|------|-------------|
| 안내(유저 앱에서 열릴 때) | `/picto`, `/disability` → `static/disability-coming-soon.html` |
| 보관 UI (그림마음) | `/disability/picto` → `static/picto.html` |
| 3D 장면 | `static/js/picto-scene.js` |
| 오프라인 번들 | `static/picto-catalog.bundle.json` (`scripts/build_picto_bundle.py`) |
| 어휘·AAC 카탈로그 | `app/services/picto_vocabulary.py` |
| API | `/api/v1/picto/catalog`, `checkin`, `chat`, `card`, `mood-timeline`, `caregiver-alert` |
| 테스트 | `tests/test_picto.py` |
| 매니페스트 요약 | `app/services/disability_product.py` → `disability_product_manifest()` |

## 포함 기능 (그림마음)

- 입체 장면 카드로 기분·욕구·도움 표현 (AAC / pictorial emotion)
- TTS·큰 터치·고대비·보호자 알림·위기 전화(1393·119·129)
- 오프라인 번들·체크인 큐

## 유저 앱에서 제거한 진입점

- 통합 앱 탭 `그림 마음` (`static/app.html`)
- PWA shortcut `그림 마음` (`static/manifest.json`)
- `/health` share_links의 「그림 마음」
- 유기체 기본 노드·추천 엣지에서 picto 제외 (`maum_organism`)

## 다음 작업 (별도 제품)

1. 도메인/앱 셸을 장애인용으로 분리
2. `/disability/picto`를 기본 홈으로 승격
3. 보호자·돌봄이 대시보드 확장
4. 유저용 앱과 세션·구독 경계 명확화
