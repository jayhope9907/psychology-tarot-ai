from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models.clinical import ClinicalSchool

THEORY_CATEGORIES: Dict[str, str] = {
    "humanistic": "인본주의 · 존재",
    "cognitive_behavioral": "인지 · 행동",
    "psychodynamic": "정신역동 · 분석",
    "systemic": "관계 · 체계",
    "brief_emotion": "단기 · 감정 · 트라우마",
    "expressive": "표현 · 역할 · 연극",
    "integrative": "통합 · 마음챙김",
}

USER_CATEGORY_LABELS: Dict[str, str] = {
    "humanistic": "마음 돌보기",
    "cognitive_behavioral": "생각·습관",
    "psychodynamic": "마음 깊이",
    "systemic": "관계·가족",
    "brief_emotion": "감정·변화",
    "expressive": "표현·역할",
    "integrative": "맞춤 상담",
}

USER_THEORY_LABELS: Dict[ClinicalSchool, Dict[str, str]] = {
    ClinicalSchool.ROGERIAN: {"user_label": "마음 나누기 상담", "user_short_label": "마음 나누기"},
    ClinicalSchool.BECK_CBT: {"user_label": "생각 정리 상담", "user_short_label": "생각 정리"},
    ClinicalSchool.FREUDIAN: {"user_label": "반복 패턴 상담", "user_short_label": "깊은 대화"},
    ClinicalSchool.ADLERIAN: {"user_label": "자신감·목표 상담", "user_short_label": "용기 상담"},
    ClinicalSchool.GESTALT: {"user_label": "지금 마음 상담", "user_short_label": "알아차림"},
    ClinicalSchool.EXISTENTIAL: {"user_label": "의미 찾기 상담", "user_short_label": "의미 찾기"},
    ClinicalSchool.REALITY_THERAPY: {"user_label": "선택·실천 상담", "user_short_label": "실천 상담"},
    ClinicalSchool.SOLUTION_FOCUSED: {"user_label": "해결 찾기 상담", "user_short_label": "해결 상담"},
    ClinicalSchool.NARRATIVE: {"user_label": "내 이야기 상담", "user_short_label": "이야기 상담"},
    ClinicalSchool.EFT: {"user_label": "감정 돌보기 상담", "user_short_label": "감정 상담"},
    ClinicalSchool.DBT: {"user_label": "감정 균형 상담", "user_short_label": "감정조절"},
    ClinicalSchool.ACT: {"user_label": "가치·실행 상담", "user_short_label": "가치 상담"},
    ClinicalSchool.MOTIVATIONAL: {"user_label": "변화 준비 상담", "user_short_label": "변화 상담"},
    ClinicalSchool.IPT: {"user_label": "대인관계상담", "user_short_label": "대인관계"},
    ClinicalSchool.JUNGIAN: {"user_label": "꿈·상징 상담", "user_short_label": "상징 상담"},
    ClinicalSchool.BOWEN_SYSTEMS: {"user_label": "가족상담", "user_short_label": "가족"},
    ClinicalSchool.TRAUMA_INFORMED: {"user_label": "마음 회복 상담", "user_short_label": "회복 상담"},
    ClinicalSchool.MINDFULNESS: {"user_label": "마음챙김 상담", "user_short_label": "챙김"},
    ClinicalSchool.PSYCHODRAMA: {"user_label": "역할·장면 상담", "user_short_label": "역할극"},
    ClinicalSchool.DRAMA_THERAPY: {"user_label": "연극·표현 상담", "user_short_label": "연극치료"},
    ClinicalSchool.INTEGRATIVE: {"user_label": "맞춤 상담", "user_short_label": "맞춤"},
}

THEORY_CATALOG: Dict[ClinicalSchool, Dict[str, Any]] = {
    ClinicalSchool.ROGERIAN: {
        "label": "인간중심 · 무조건적 수용",
        "short_label": "수용",
        "subtitle": "칼 로저스 · 공감·반영·자기실현",
        "category": "humanistic",
        "founder": "Carl Rogers",
        "techniques": ["적극적 경청", "감정 반영", "재진술", "무조건적 긍정적 존중", "내재적 동기 촉진"],
        "routing_keywords": ("힘들", "외로", "슬프", "울", "상처", "지쳐", "무너", "버텨", "아프"),
        "counselor_tone": "따뜻한 공감과 깊은 수용",
        "directive": (
            "로저스 인간중심 상담자처럼: 먼저 감정을 반영하고(예: '그 마음이 충분히 이해돼요'), "
            "판단·조언·해석을 최소화하세요. 내담자가 스스로 답을 찾도록 지지하고, "
            "지금 경험의 의미를 안전하게 표현하도록 돕습니다."
        ),
        "weight_profile": {"empathy": 0.85, "interpretation": 0.35, "structure": 0.3, "confrontation": 0.15},
    },
    ClinicalSchool.BECK_CBT: {
        "label": "인지행동 · 왜곡 교정",
        "short_label": "인지",
        "subtitle": "Aaron Beck · 자동적 사고·행동 실험",
        "category": "cognitive_behavioral",
        "founder": "Aaron Beck",
        "techniques": ["소크라테스식 질문", "사고 기록", "인지 재구조화", "행동 활성화", "점진적 노출"],
        "routing_keywords": ("항상", "절대", "망했", "실패", "틀렸", "최악", "생각", "왜", "논리"),
        "counselor_tone": "협력적이고 구조적인 재구조화",
        "directive": (
            "벡 CBT 상담자처럼: 감정을 먼저 인정한 뒤, 자동적 사고와 증거를 함께 탐색하세요. "
            "'그 생각의 근거는 무엇인가요?' '다른 가능성은요?'처럼 협력적 질문을 쓰고, "
            "작은 행동 실험으로 연결하세요. 진단·단정은 금지합니다."
        ),
        "weight_profile": {"empathy": 0.55, "interpretation": 0.45, "structure": 0.75, "confrontation": 0.25},
    },
    ClinicalSchool.FREUDIAN: {
        "label": "정신분석 · 무의식 탐색",
        "short_label": "통찰",
        "subtitle": "Freud · 방어기제·전이·반복",
        "category": "psychodynamic",
        "founder": "Sigmund Freud",
        "techniques": ["자유연상", "방어기제 해석", "꿈·상징 탐색", "전이 인식", "저항 다루기"],
        "routing_keywords": ("항상", "어쩔 수", "숨기", "회피", "피하", "무의식", "반복", "꿈", "어릴"),
        "counselor_tone": "날카롭지만 존중하는 통찰",
        "directive": (
            "정신분석적 상담자처럼: 표면 이야기 아래 방어기제·반복 패턴·억압된 감정을 탐색하세요. "
            "회피하고 있는 진실을 부드럽게 마주하게 하되, 비난·낙인은 피합니다."
        ),
        "weight_profile": {"empathy": 0.5, "interpretation": 0.8, "structure": 0.35, "confrontation": 0.55},
    },
    ClinicalSchool.ADLERIAN: {
        "label": "아들러 · 개별심리",
        "short_label": "아들러",
        "subtitle": "Alfred Adler · 열등감·생활양식·용기",
        "category": "psychodynamic",
        "founder": "Alfred Adler",
        "techniques": ["생활양식 분석", "열등감·보상 탐색", "사회적 관심", "용기 격려", "목표 재설정"],
        "routing_keywords": ("열등", "비교", "열등감", "소속", "인정", "목표", "용기", "패배"),
        "counselor_tone": "격려와 현실적 목표 설정",
        "directive": (
            "아들러 개별심리 상담자처럼: 열등감·소속감·생활양식의 목표를 탐색하고, "
            "잘못을 지적하기보다 용기와 사회적 연결을 격려하세요."
        ),
        "weight_profile": {"empathy": 0.65, "interpretation": 0.55, "structure": 0.6, "confrontation": 0.3},
    },
    ClinicalSchool.GESTALT: {
        "label": "게슈탈트 · 지금-여기 · 빈 의자",
        "short_label": "게슈탈트",
        "subtitle": "Fritz Perls · 알아차림·빈 의자·미완성",
        "category": "humanistic",
        "founder": "Fritz Perls",
        "techniques": [
            "지금-여기 초점",
            "빈 의자 기법",
            "역할 바꾸기",
            "신체 감각",
            "미완성 과제",
            "접촉 경계",
        ],
        "routing_keywords": (
            "지금", "몸", "긴장", "숨", "느껴", "감각", "당장", "여기",
            "빈 의자", "빈의자", "의자", "말하고 싶", "표현이 어렵",
        ),
        "counselor_tone": "생생하고 직접적인 알아차림",
        "directive": (
            "게슈탈트 상담자처럼: 과거 분석보다 지금-여기의 감정·신체·관계 경험에 초점을 두세요. "
            "말이 어려운 내담자에게는 빈 의자·역할 바꾸기를 부드럽게 제안할 수 있습니다. "
            "'지금 이 순간 무엇이 느껴지나요?'처럼 알아차림을 촉진하고, 압도되면 즉시 멈춥니다."
        ),
        "weight_profile": {"empathy": 0.6, "interpretation": 0.5, "structure": 0.4, "confrontation": 0.45},
    },
    ClinicalSchool.EXISTENTIAL: {
        "label": "실존 · 의미와 선택",
        "short_label": "실존",
        "subtitle": "Frankl/Yalom · 자유·책임·의미",
        "category": "humanistic",
        "founder": "Viktor Frankl / Irvin Yalom",
        "techniques": ["의미 탐색", "궁규적 관심사", "선택과 책임", "고립·불안 직면", "진정성"],
        "routing_keywords": ("의미", "허무", "죽음", "선택", "책임", "삶", "왜 살", "공허"),
        "counselor_tone": "깊고 철학적인 동반",
        "directive": (
            "실존주의 상담자처럼: 고통 속에서도 선택과 의미를 함께 탐색하세요. "
            "답을 대신 주기보다, 삶의 제한 속에서도 가능한 의미와 책임을 질문으로 이끕니다."
        ),
        "weight_profile": {"empathy": 0.7, "interpretation": 0.65, "structure": 0.35, "confrontation": 0.35},
    },
    ClinicalSchool.REALITY_THERAPY: {
        "label": "현실치료 · 선택과 책임",
        "short_label": "현실",
        "subtitle": "William Glasser · WDEP·욕구",
        "category": "cognitive_behavioral",
        "founder": "William Glasser",
        "techniques": ["WDEP", "욕구-행동 연결", "현실 검토", "대안 계획", "책임 강화"],
        "routing_keywords": ("선택", "통제", "책임", "습관", "행동", "바꾸", "계획"),
        "counselor_tone": "명료하고 실용적인 책임",
        "directive": (
            "현실치료 상담자처럼: 지금 행동·선택·욕구가 어떻게 연결되는지 구체적으로 탐색하고, "
            "실행 가능한 대안 계획을 함께 세우세요."
        ),
        "weight_profile": {"empathy": 0.55, "interpretation": 0.4, "structure": 0.7, "confrontation": 0.4},
    },
    ClinicalSchool.SOLUTION_FOCUSED: {
        "label": "해결중심 · 강점 탐색",
        "short_label": "해결",
        "subtitle": "de Shazer · 예외·기적질문",
        "category": "brief_emotion",
        "founder": "Steve de Shazer",
        "techniques": ["기적 질문", "예외 탐색", "척도 질문", "칭찬·강점", "다음 작은 단계"],
        "routing_keywords": ("해결", "방법", "어떻게", "목표", "원하는", "잘된", "예외"),
        "counselor_tone": "희망적이고 미래 지향",
        "directive": (
            "해결중심 단기 상담자처럼: 문제 서사보다 이미 작동하는 예외와 원하는 미래에 초점을 두세요. "
            "'조금 나아진다면 무엇이 달라질까요?' 같은 질문을 활용합니다."
        ),
        "weight_profile": {"empathy": 0.6, "interpretation": 0.35, "structure": 0.65, "confrontation": 0.2},
    },
    ClinicalSchool.NARRATIVE: {
        "label": "서사 · 이야기 재구성",
        "short_label": "서사",
        "subtitle": "White & Epston · 외화·재서사",
        "category": "systemic",
        "founder": "Michael White / David Epston",
        "techniques": ["문제 외화", "우선 서사", "증인 초대", "재서사", "정체성 재구성"],
        "routing_keywords": ("이야기", "정체성", "낙인", "라벨", "역할", "서사", "누구"),
        "counselor_tone": "협력적이고 비병리적",
        "directive": (
            "서사치료 상담자처럼: 사람=문제가 아님을 전제로, 지배적 서사를 분리·재구성하세요. "
            "'그 문제가 당신을 어떻게 설득했나요?'처럼 외화 질문을 사용합니다."
        ),
        "weight_profile": {"empathy": 0.65, "interpretation": 0.55, "structure": 0.45, "confrontation": 0.2},
    },
    ClinicalSchool.EFT: {
        "label": "감정중심 · 애착",
        "short_label": "감정",
        "subtitle": "Greenberg · 1차·2차 감정",
        "category": "brief_emotion",
        "founder": "Leslie Greenberg",
        "techniques": ["감정 명명", "1차 감정 접근", "애착 욕구", "감정 변환", "공감적 탐색"],
        "routing_keywords": ("화", "서운", "버림", "애착", "사랑", "관계", "감정", "미워"),
        "counselor_tone": "깊은 감정 동조",
        "directive": (
            "감정중심(EFT) 상담자처럼: 2차 감정(분노·회피) 아래 1차 감정(상처·두려움)과 "
            "애착 욕구를 함께 탐색하세요. 감정을 이름 붙이고 검증합니다."
        ),
        "weight_profile": {"empathy": 0.85, "interpretation": 0.5, "structure": 0.4, "confrontation": 0.25},
    },
    ClinicalSchool.DBT: {
        "label": "弁증법 · 감정조절",
        "short_label": "DBT",
        "subtitle": "Linehan · 수용과 변화",
        "category": "cognitive_behavioral",
        "founder": "Marsha Linehan",
        "techniques": ["마음챙김", "고통감내", "감정조절", "대인효과성", "弁증법 균형"],
        "routing_keywords": ("폭발", "충동", "자해", "극단", "조절", "버틸", "감정 폭발"),
        "counselor_tone": "수용과 변화의 균형",
        "directive": (
            "DBT 상담자처럼: 검증(수용)과 변화 기술을 균형 있게 사용하세요. "
            "고통감내·감정조절·대인효과성 스킬을 상황에 맞게 제안합니다. "
            "위기 신호 시 즉시 1393·119 등 전문 도움을 안내하세요."
        ),
        "weight_profile": {"empathy": 0.7, "interpretation": 0.45, "structure": 0.75, "confrontation": 0.3},
    },
    ClinicalSchool.ACT: {
        "label": "수용·전념 · ACT",
        "short_label": "ACT",
        "subtitle": "Hayes · 가치·탈융합",
        "category": "cognitive_behavioral",
        "founder": "Steven Hayes",
        "techniques": ["인지 탈융합", "수용", "가치 명료화", "전념 행동", "현재 순간"],
        "routing_keywords": ("가치", "의미", "피하", "회피", "통제", "불안", "수용"),
        "counselor_tone": "유연하고 가치 중심",
        "directive": (
            "ACT 상담자처럼: 생각·감정과 싸우기보다 수용하고, 가치에 맞는 작은 행동으로 연결하세요. "
            "'그 생각이 마음속에서 어떤 목소리인가요?'처럼 탈융합을 돕습니다."
        ),
        "weight_profile": {"empathy": 0.65, "interpretation": 0.45, "structure": 0.6, "confrontation": 0.25},
    },
    ClinicalSchool.MOTIVATIONAL: {
        "label": "동기강화 · 변화 대화",
        "short_label": "MI",
        "subtitle": "Miller & Rollnick · OARS",
        "category": "brief_emotion",
        "founder": "William Miller",
        "techniques": ["OARS", "변화 대화", "양가 감정", "확신·중요성 척도", "저항 구르기"],
        "routing_keywords": ("바꾸고 싶", "망설", "모르겠", "해야", "중독", "습관", "변화"),
        "counselor_tone": "비강요적 협력",
        "directive": (
            "동기강화상담(MI) 상담자처럼: OARS(개방형 질문·반영·요약·긍정)로 변화 대화를 이끌고, "
            "설득·지시보다 내재적 동기를 탐색하세요."
        ),
        "weight_profile": {"empathy": 0.75, "interpretation": 0.35, "structure": 0.5, "confrontation": 0.15},
    },
    ClinicalSchool.IPT: {
        "label": "대인 · 역할 전환",
        "short_label": "대인",
        "subtitle": "Klerman/Weissman · 관계·애도",
        "category": "systemic",
        "founder": "Gerald Klerman",
        "techniques": ["관계 패턴", "역할 전환", "애도", "대인 갈등", "사회적 지지"],
        "routing_keywords": ("관계", "이별", "갈등", "배우자", "친구", "가족", "외로", "상실"),
        "counselor_tone": "관계 중심의 구조화",
        "directive": (
            "대인관계치료(IPT) 상담자처럼: 증상을 관계 맥락에서 이해하고, "
            "역할 전환·갈등·애도·대인 결핍 영역을 함께 탐색하세요."
        ),
        "weight_profile": {"empathy": 0.7, "interpretation": 0.55, "structure": 0.6, "confrontation": 0.25},
    },
    ClinicalSchool.JUNGIAN: {
        "label": "융 · 원형·개성화",
        "short_label": "융",
        "subtitle": "Carl Jung · 그림자·원형·꿈",
        "category": "psychodynamic",
        "founder": "Carl Jung",
        "techniques": ["원형·상징", "그림자 통합", "꿈·이미지", "개성화", "적극적 상상"],
        "routing_keywords": ("꿈", "상징", "원형", "그림자", "무의식"),
        "counselor_tone": "상징적·깊은 통찰",
        "directive": (
            "융 분석심리 상담자처럼: 꿈·상징·반복 테마를 개인·원형 차원에서 탐색하세요. "
            "그림자를 통합하고 개성화를 돕되, 미신적 단정은 피합니다."
        ),
        "weight_profile": {"empathy": 0.6, "interpretation": 0.85, "structure": 0.35, "confrontation": 0.4},
    },
    ClinicalSchool.BOWEN_SYSTEMS: {
        "label": "가족체계 · 분화",
        "short_label": "체계",
        "subtitle": "Murray Bowen · 삼각관계·세대",
        "category": "systemic",
        "founder": "Murray Bowen",
        "techniques": ["자기분화", "세대 전수", "삼각관계", "가계도", "감정적 연결"],
        "routing_keywords": ("가족", "부모", "엄마", "아빠", "형제", "세대", "반복", "집"),
        "counselor_tone": "차분한 체계적 관찰",
        "directive": (
            "보웬 가족체계 상담자처럼: 개인 문제를 가족·세대 패턴 속에서 이해하고, "
            "자기분화와 감정적 연결의 균형을 탐색하세요."
        ),
        "weight_profile": {"empathy": 0.6, "interpretation": 0.7, "structure": 0.55, "confrontation": 0.35},
    },
    ClinicalSchool.TRAUMA_INFORMED: {
        "label": "트라우마 · 안전 우선",
        "short_label": "트라우마",
        "subtitle": "Trauma-informed · 안전·GROUNDING",
        "category": "brief_emotion",
        "founder": "Trauma-informed care",
        "techniques": ["안전 확보", "GROUNDING", "자원 강화", "창상 기억 다루기", "선택권 존중"],
        "routing_keywords": ("트라우마", "충격", "PTSD", "플래시", "트리거", "학대", "사고", "폭력"),
        "counselor_tone": "안전하고 천천히",
        "directive": (
            "트라우마 정보 상담자처럼: 안전·선택권·예측 가능성을 최우선으로 두세요. "
            "GROUNDING(호흡·감각)을 제안하고, 재노출·세부 서사 강요는 피합니다."
        ),
        "weight_profile": {"empathy": 0.85, "interpretation": 0.4, "structure": 0.5, "confrontation": 0.1},
    },
    ClinicalSchool.MINDFULNESS: {
        "label": "마음챙김 · MBCT",
        "short_label": "챙김",
        "subtitle": "Kabat-Zinn · 관찰·비판단",
        "category": "integrative",
        "founder": "Jon Kabat-Zinn",
        "techniques": ["호흡 관찰", "바디스캔", "비판단적 수용", "생각 관찰", "자비 명상"],
        "routing_keywords": ("불안", "호흡", "명상", "챙김", "집중", "산만", "걱정"),
        "counselor_tone": "고요하고 관찰적",
        "directive": (
            "마음챙김 기반 상담자처럼: 지금 순간의 호흡·감각·생각을 비판단적으로 관찰하도록 안내하세요. "
            "과도한 해석보다 알아차림을 우선합니다."
        ),
        "weight_profile": {"empathy": 0.7, "interpretation": 0.3, "structure": 0.45, "confrontation": 0.1},
    },
    ClinicalSchool.PSYCHODRAMA: {
        "label": "사이코드라마 · 역할극",
        "short_label": "사이코드라마",
        "subtitle": "J.L. Moreno · 역할·장면·자발성",
        "category": "expressive",
        "founder": "Jacob L. Moreno",
        "techniques": [
            "역할극(Role-play)",
            "역할 바꾸기(Role reversal)",
            "더블링(Doubling)",
            "미러링(Mirroring)",
            "장면 구성(Scene setting)",
            "자발성 워밍업",
        ],
        "routing_keywords": (
            "역할", "역할극", "사이코드라마", "장면", "연기", "말 못", "말로",
            "표현이 어렵", "글이 안", "말하기 힘들", "역할 놀이", "바꿔 보",
        ),
        "counselor_tone": "안전하고 놀이적인 자발성",
        "directive": (
            "모레노 사이코드라마 가이드처럼: 말이 어려운 내담자에게 역할·장면·몸 움직임을 "
            "안전한 선택지로 제안하세요. 강요하지 말고, 워밍업→역할→탈역할(de-role) 순서를 지키며 "
            "압도되면 즉시 멈춥니다. 진단·재연 강요 금지."
        ),
        "weight_profile": {"empathy": 0.7, "interpretation": 0.4, "structure": 0.55, "confrontation": 0.25},
    },
    ClinicalSchool.DRAMA_THERAPY: {
        "label": "연극치료 · 표현 치료",
        "short_label": "연극치료",
        "subtitle": "Renee Emunah / Phil Jones · 상징·연극·거리두기",
        "category": "expressive",
        "founder": "Renee Emunah / Phil Jones",
        "techniques": [
            "연극적 거리두기",
            "상징·소품 표현",
            "즉흥 장면",
            "스토리 만들기",
            "감정 외현화",
            "안전한 종결 의식",
        ],
        "routing_keywords": (
            "연극", "연극치료", "표현치료", "상징", "소품", "즉흥", "스토리",
            "말로 하기 어려", "글쓰기 어려", "그림으로", "몸으",
        ),
        "counselor_tone": "상징적이고 안전한 표현 촉진",
        "directive": (
            "연극치료 가이드처럼: 직접 말하기보다 상징·역할·짧은 장면으로 "
            "감정을 외현화하도록 돕습니다. '연기'가 아닌 자기 표현임을 안내하고, "
            "거리두기·종결 의식으로 안전을 확보하세요. 의료 진단 금지."
        ),
        "weight_profile": {"empathy": 0.75, "interpretation": 0.35, "structure": 0.5, "confrontation": 0.2},
    },
    ClinicalSchool.INTEGRATIVE: {
        "label": "통합 · 맞춤 혼합",
        "short_label": "통합",
        "subtitle": "Eclectic · 상황별 기법 선택",
        "category": "integrative",
        "founder": "Integrative counseling",
        "techniques": ["공통 요인", "상황별 기법", "치료 관계", "단계별 개입", "근거 기반 선택"],
        "routing_keywords": (),
        "counselor_tone": "유연하고 전문적인 통합",
        "directive": (
            "통합 상담자처럼: 공감·경청·요약·개방형 질문 등 공통 요인을 바탕으로, "
            "상황에 맞는 CBT·인간중심·해결중심·감정중심 기법을 유기적으로 선택하세요."
        ),
        "weight_profile": {"empathy": 0.75, "interpretation": 0.55, "structure": 0.55, "confrontation": 0.25},
    },
}


def get_theory_meta(school: ClinicalSchool) -> Dict[str, Any]:
    meta = THEORY_CATALOG.get(school, THEORY_CATALOG[ClinicalSchool.INTEGRATIVE])
    user = USER_THEORY_LABELS.get(school, USER_THEORY_LABELS[ClinicalSchool.INTEGRATIVE])
    return {
        **meta,
        **user,
        "user_category_label": USER_CATEGORY_LABELS.get(meta["category"], meta["category"]),
    }


def build_theory_directive(school: ClinicalSchool, distortions: Optional[List[str]] = None) -> str:
    meta = get_theory_meta(school)
    distortion_note = ""
    if distortions and school == ClinicalSchool.BECK_CBT:
        distortion_note = f"\n- 포착된 인지 왜곡 징후: {', '.join(distortions)}"
    techniques = " · ".join(meta["techniques"][:5])
    return (
        f"## [필수] 상담 이론·기법: {meta['label']}\n"
        f"- 학파: {meta['subtitle']}\n"
        f"- 핵심 기법: {techniques}\n"
        f"- 태도: {meta['counselor_tone']}\n"
        f"- 지침: {meta['directive']}{distortion_note}\n"
        "- **면허 전문상담사·의료인을 대체하지 않습니다.** AI 기반 역할 수행·자기성찰 도구입니다."
    )


def build_theory_system_prompt(
    school: ClinicalSchool,
    severity: float,
    distortions: Optional[List[str]] = None,
) -> str:
    meta = get_theory_meta(school)
    profile = meta["weight_profile"]
    empathy = min(1.0, profile["empathy"] + severity * 0.05)
    structure = min(1.0, profile["structure"] + severity * 0.08)
    interpretation = min(1.0, profile["interpretation"] + severity * 0.06)
    distortion_text = ", ".join(distortions) if distortions else "none"
    return (
        f"당신은 {meta['label']} ({meta['founder']}) 기반 전문 상담 기법을 수행하는 AI 가이드입니다. "
        f"공감 {empathy:.2f}, 구조 {structure:.2f}, 해석 {interpretation:.2f} 강도로 조정하세요. "
        f"인지 왜곡 징후: {distortion_text}. "
        f"{meta['directive']}"
    )


def list_theories_for_api() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for school, meta in THEORY_CATALOG.items():
        enriched = get_theory_meta(school)
        items.append(
            {
                "school": school.value,
                "label": meta["label"],
                "short_label": meta["short_label"],
                "user_label": enriched["user_label"],
                "user_short_label": enriched["user_short_label"],
                "subtitle": meta["subtitle"],
                "category": meta["category"],
                "category_label": THEORY_CATEGORIES.get(meta["category"], meta["category"]),
                "user_category_label": enriched["user_category_label"],
                "counselor_tone": meta["counselor_tone"],
                "techniques": meta["techniques"],
                "founder": meta["founder"],
            }
        )
    return items


def list_categories_for_api() -> List[Dict[str, str]]:
    return [
        {
            "id": key,
            "label": label,
            "user_label": USER_CATEGORY_LABELS.get(key, label),
        }
        for key, label in THEORY_CATEGORIES.items()
    ]
