# Backend Architecture for Psychology Tarot AI

## 1. 목표
- 내담자의 심리 상태를 정교하게 리딩하고, 인지행동치료(CBT) 관점에서 현실적인 상담 조언을 제공한다.
- 타로 카드 해석과 상담 심리학적 프레임워크를 결합한 응답을 안정적으로 생성한다.
- 향후 대화 기억, 사용자 세션, 상담 이력, 평가 메트릭 확장을 수용할 수 있는 구조로 설계한다.

## 2. 핵심 구성 요소
### 2.1 API Layer
- FastAPI 기반의 `/consult` 엔드포인트를 통해 사용자 입력을 수신한다.
- 요청 스키마는 `user_story`, `drawn_card`를 포함하도록 구성한다.
- 응답은 상담 분석 텍스트를 JSON 형태로 반환하도록 확장 가능하다.

### 2.2 Service Layer
- `ConsultationService`는 사용자 입력을 정규화하고, 프롬프트를 생성하며, 모델 호출을 관리한다.
- 상담 목표, 심리 상태 리딩 기준, CBT 개입 포인트를 서비스 로직으로 분리한다.

### 2.3 Prompt Orchestration Layer
- 시스템 프롬프트와 사용자 프롬프트를 분리하여 재사용 가능하게 구성한다.
- 프롬프트는 심리적 공감, 비판 없는 수용, 행동 실천 유도, 위험 상황 인지, 응답 형식 규칙을 포함해야 한다.

### 2.4 Model Integration Layer
- OpenAI Chat Completion API를 활용하되, 모델 선택은 `gpt-4o-mini`를 기본값으로 둔다.
- 추후 `gpt-4.1` 또는 모델별 전문화 전략으로 확장할 수 있다.

### 2.5 Safety & Guardrails
- 위기 상황(자해/자살/폭력) 감지 시 전문적 개입을 권고하는 규칙을 포함한다.
- 상담 응답은 비판적 판단 대신 공감적, 수용적, 현실적인 조언을 우선한다.

### 2.6 Persistence & Analytics
- 상담 세션 기록, 카드별 응답 패턴, 사용자 만족도, 상담 효과 지표를 저장할 수 있도록 설계한다.
- 향후 PostgreSQL 또는 Supabase와 연계할 수 있다.

## 3. 권장 폴더 구조
```text
app/
  main.py
  prompt_config.py
  services/
    consultation_service.py
  models/
    request_schemas.py
  utils/
    safety.py
  tests/
    test_consultation.py
docs/
  backend_architecture.md
  prompt_guidelines.md
```

## 4. 요청 처리 흐름
1. 클라이언트가 상담 요청을 전송한다.
2. FastAPI가 요청을 검증한다.
3. 서비스 계층이 사용자 맥락과 카드 정보를 정리한다.
4. 프롬프트 구성 모듈이 시스템 프롬프트와 사용자 입력을 조합한다.
5. 모델이 응답을 생성하고, 서비스가 후속 포맷을 정리한다.
6. 결과를 API 응답으로 반환한다.

## 5. 설계 원칙
- 공감과 수용을 최우선으로 한다.
- CBT 기반의 인지 재구성, 행동 실천, 자기 관찰을 권장한다.
- 타로는 심리적 상징과 성찰 도구로 활용하되, 과장된 확신을 주지 않는다.
- 응답은 구체적이고 실행 가능해야 한다.
