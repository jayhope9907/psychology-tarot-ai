"""Additional counseling psychology theories merged into THEORY_CATALOG."""
from __future__ import annotations

from typing import Any, Dict

from app.models.clinical import ClinicalSchool

EXTRA_USER_LABELS: Dict[ClinicalSchool, Dict[str, str]] = {
    ClinicalSchool.LOGOTHERAPY: {"user_label": "의미·목적 상담", "user_short_label": "의미치료"},
    ClinicalSchool.REBT: {"user_label": "합리적 생각 상담", "user_short_label": "REBT"},
    ClinicalSchool.SCHEMA_THERAPY: {"user_label": "스키마·패턴 상담", "user_short_label": "스키마"},
    ClinicalSchool.MBCT: {"user_label": "마음챙김 인지상담", "user_short_label": "MBCT"},
    ClinicalSchool.CFT: {"user_label": "자기자비 상담", "user_short_label": "자비상담"},
    ClinicalSchool.OBJECT_RELATIONS: {"user_label": "관계 내면 상담", "user_short_label": "대상관계"},
    ClinicalSchool.SELF_PSYCHOLOGY: {"user_label": "자기 돌봄 상담", "user_short_label": "자기심리"},
    ClinicalSchool.TRANSACTIONAL_ANALYSIS: {"user_label": "교류분석 상담", "user_short_label": "TA"},
    ClinicalSchool.STRUCTURAL_FAMILY: {"user_label": "가족구조 상담", "user_short_label": "구조가족"},
    ClinicalSchool.SATIR: {"user_label": "사티어 가족상담", "user_short_label": "사티어"},
    ClinicalSchool.STRATEGIC_FAMILY: {"user_label": "전략적 가족상담", "user_short_label": "전략가족"},
    ClinicalSchool.ATTACHMENT: {"user_label": "애착 상담", "user_short_label": "애착"},
    ClinicalSchool.EMDR_INFORMED: {"user_label": "외상 재처리 안내", "user_short_label": "EMDR안내"},
    ClinicalSchool.ART_THERAPY: {"user_label": "미술·표현 상담", "user_short_label": "미술치료"},
    ClinicalSchool.MUSIC_THERAPY: {"user_label": "음악 표현 상담", "user_short_label": "음악치료"},
    ClinicalSchool.DANCE_MOVEMENT: {"user_label": "몸·움직임 상담", "user_short_label": "무용치료"},
    ClinicalSchool.PLAY_THERAPY: {"user_label": "놀이 표현 상담", "user_short_label": "놀이치료"},
    ClinicalSchool.SANDPLAY: {"user_label": "모래놀이 상담", "user_short_label": "모래놀이"},
    ClinicalSchool.POSITIVE_PSYCHOLOGY: {"user_label": "강점·행복 상담", "user_short_label": "긍정심리"},
    ClinicalSchool.FEMINIST: {"user_label": "페미니스트 상담", "user_short_label": "페미니스트"},
    ClinicalSchool.MULTICULTURAL: {"user_label": "다문화 상담", "user_short_label": "다문화"},
}

EXTRA_THEORIES: Dict[ClinicalSchool, Dict[str, Any]] = {
    ClinicalSchool.LOGOTHERAPY: {
        "label": "의미치료 · 로고테라피",
        "short_label": "로고테라피",
        "subtitle": "Viktor Frankl · 의미·선택·책임",
        "category": "humanistic",
        "founder": "Viktor Frankl",
        "techniques": ["의미 탐색", "역설의도", "태도 수정", "가치 명료화", "선택 책임"],
        "routing_keywords": ("의미", "목적", "왜 살", "허무", "공허", "책임", "선택", "로고"),
        "counselor_tone": "존중하는 의미·선택 탐색",
        "directive": (
            "프랑클 의미치료 가이드처럼: 고통 속에서도 선택·태도·의미를 함께 탐색하세요. "
            "강요된 긍정은 피하고, 내담자의 고유한 가치를 존중합니다. 의료 진단 금지."
        ),
        "weight_profile": {"empathy": 0.7, "interpretation": 0.55, "structure": 0.45, "confrontation": 0.35},
    },
    ClinicalSchool.REBT: {
        "label": "합리적 정서행동 · REBT",
        "short_label": "REBT",
        "subtitle": "Albert Ellis · ABC·비합리적 신념",
        "category": "cognitive_behavioral",
        "founder": "Albert Ellis",
        "techniques": ["ABC 모형", "논박(Dispute)", "합리적 대안", "숙제", "유머·직면"],
        "routing_keywords": ("해야 해", "반드시", "망했어", "바보", "비합리", "논박", "REBT", "절대"),
        "counselor_tone": "직접적이되 존중하는 논박",
        "directive": (
            "엘리스 REBT처럼: ABC로 활성화 사건·신념·결과를 정리하고, "
            "비합리적 신념을 부드럽게 논박한 뒤 합리적 대안으로 연결하세요. 낙인 금지."
        ),
        "weight_profile": {"empathy": 0.45, "interpretation": 0.5, "structure": 0.8, "confrontation": 0.55},
    },
    ClinicalSchool.SCHEMA_THERAPY: {
        "label": "스키마 치료",
        "short_label": "스키마",
        "subtitle": "Jeffrey Young · 초기부적응 스키마·모드",
        "category": "cognitive_behavioral",
        "founder": "Jeffrey Young",
        "techniques": ["스키마 탐색", "모드 작업", "제한된 재양육", "이미지 재구성", "인지·행동 기법"],
        "routing_keywords": ("스키마", "패턴", "늘 그래", "어린 나", "버림", "결함", "모드"),
        "counselor_tone": "따뜻한 재양육과 패턴 인식",
        "directive": (
            "영 스키마 치료처럼: 반복 패턴·모드(비판자/취약아 등)를 명명하고, "
            "제한된 재양육·이미지 작업으로 돌봄을 제공하세요. 진단 단정 금지."
        ),
        "weight_profile": {"empathy": 0.75, "interpretation": 0.65, "structure": 0.65, "confrontation": 0.3},
    },
    ClinicalSchool.MBCT: {
        "label": "마음챙김 기반 인지치료 · MBCT",
        "short_label": "MBCT",
        "subtitle": "Segal · Williams · Teasdale",
        "category": "cognitive_behavioral",
        "founder": "Zindel Segal / Mark Williams / John Teasdale",
        "techniques": ["몸 스캔", "3분 호흡공간", "생각 관찰", "탈동일시", "재발 예방"],
        "routing_keywords": ("마음챙김", "MBCT", "반추", "되풀이", "호흡", "관찰", "재발"),
        "counselor_tone": "차분한 관찰·탈동일시",
        "directive": (
            "MBCT 가이드처럼: 생각과 감정을 '사실'이 아닌 '사건'으로 관찰하도록 돕고, "
            "짧은 호흡·몸 알아차림으로 반추 고리를 부드럽게 끊습니다."
        ),
        "weight_profile": {"empathy": 0.7, "interpretation": 0.35, "structure": 0.7, "confrontation": 0.15},
    },
    ClinicalSchool.CFT: {
        "label": "연민중심치료 · CFT",
        "short_label": "CFT",
        "subtitle": "Paul Gilbert · 자기자비·안정화",
        "category": "cognitive_behavioral",
        "founder": "Paul Gilbert",
        "techniques": ["안전장소 이미지", "자기자비 문장", "위협·추동·안정 체계", "연민적 자기", "호흡 안정"],
        "routing_keywords": ("자비", "수치", "자기비난", "연민", "안전", "CFT", "부끄"),
        "counselor_tone": "온화한 자비·안정화",
        "directive": (
            "길버트 CFT처럼: 자기비난·수치를 위협체계로 이해하고, "
            "안정·연민 체계를 키우는 이미지·문장을 함께 연습하세요."
        ),
        "weight_profile": {"empathy": 0.85, "interpretation": 0.4, "structure": 0.55, "confrontation": 0.15},
    },
    ClinicalSchool.OBJECT_RELATIONS: {
        "label": "대상관계 이론",
        "short_label": "대상관계",
        "subtitle": "Klein · Winnicott · Fairbairn",
        "category": "psychodynamic",
        "founder": "Melanie Klein / D.W. Winnicott",
        "techniques": ["내면 대상 탐색", "전이 이해", "홀딩 환경", "분열·통합", "관계 패턴"],
        "routing_keywords": ("대상관계", "홀딩", "분열", "내면화", "관계 반복", "위니콧"),
        "counselor_tone": "관계 속 내면 대상 탐색",
        "directive": (
            "대상관계 관점으로: 중요한 타인이 내면에 어떻게 자리했는지, "
            "관계 반복이 어떻게 이어지는지 안전하게 탐색합니다. 해석은 천천히."
        ),
        "weight_profile": {"empathy": 0.65, "interpretation": 0.75, "structure": 0.35, "confrontation": 0.4},
    },
    ClinicalSchool.SELF_PSYCHOLOGY: {
        "label": "자기심리학",
        "short_label": "자기심리",
        "subtitle": "Heinz Kohut · 자기대상·공감",
        "category": "psychodynamic",
        "founder": "Heinz Kohut",
        "techniques": ["공감적 몰입", "자기대상 경험", "이상화·반영", "자기존중 회복", "미시적 실패 수리"],
        "routing_keywords": ("자기존중", "공허", "인정", "자기대상", "코헛", "반영"),
        "counselor_tone": "깊이 있는 공감적 반영",
        "directive": (
            "코헛 자기심리학처럼: 공감적 반영으로 자기존중·자기응집감을 지지하고, "
            "이상화·반영 욕구를 존중하세요. 비판적 해석은 최소화합니다."
        ),
        "weight_profile": {"empathy": 0.9, "interpretation": 0.55, "structure": 0.3, "confrontation": 0.15},
    },
    ClinicalSchool.TRANSACTIONAL_ANALYSIS: {
        "label": "교류분석 · TA",
        "short_label": "TA",
        "subtitle": "Eric Berne · Parent-Adult-Child",
        "category": "psychodynamic",
        "founder": "Eric Berne",
        "techniques": ["자아상태(P-A-C)", "교류 분석", "게임 인식", "각본 분석", "재결정"],
        "routing_keywords": ("교류분석", "자아상태", "부모자아", "아동자아", "각본", "TA", "게임"),
        "counselor_tone": "명료한 교류·각본 탐색",
        "directive": (
            "번 교류분석처럼: Parent-Adult-Child 자아상태와 교류 패턴을 함께 보고, "
            "반복되는 '게임'·인생 각본을 부드럽게 인식하도록 돕습니다."
        ),
        "weight_profile": {"empathy": 0.6, "interpretation": 0.65, "structure": 0.7, "confrontation": 0.35},
    },
    ClinicalSchool.STRUCTURAL_FAMILY: {
        "label": "구조적 가족치료",
        "short_label": "구조가족",
        "subtitle": "Salvador Minuchin · 경계·하위체계",
        "category": "systemic",
        "founder": "Salvador Minuchin",
        "techniques": ["경계 명료화", "합류(joining)", "재구조화", "동맹·연합", "가족 지도"],
        "routing_keywords": ("가족구조", "경계", "삼각", "미누친", "하위체계", "재구조"),
        "counselor_tone": "명확한 구조·경계 탐색",
        "directive": (
            "미누친 구조적 가족치료처럼: 경계·동맹·하위체계를 파악하고, "
            "더 기능적인 구조를 향해 작은 재배치를 제안하세요. 비난은 피합니다."
        ),
        "weight_profile": {"empathy": 0.55, "interpretation": 0.6, "structure": 0.8, "confrontation": 0.4},
    },
    ClinicalSchool.SATIR: {
        "label": "사티어 경험적 가족치료",
        "short_label": "사티어",
        "subtitle": "Virginia Satir · 의사소통·자존감",
        "category": "systemic",
        "founder": "Virginia Satir",
        "techniques": ["의사소통 자세", "가족 조각", "자존감 자원", " Congruence", "온도계"],
        "routing_keywords": ("사티어", "의사소통", "자존감", "가족조각", "일치", "비난 자세"),
        "counselor_tone": "따뜻하고 성장 지향적",
        "directive": (
            "사티어처럼: 비난·회유·초이성·산만 자세를 알아차리고, "
            "일치(congruence)·자존감·성장 가능성을 중심으로 관계를 돕습니다."
        ),
        "weight_profile": {"empathy": 0.8, "interpretation": 0.45, "structure": 0.5, "confrontation": 0.25},
    },
    ClinicalSchool.STRATEGIC_FAMILY: {
        "label": "전략적 가족치료",
        "short_label": "전략가족",
        "subtitle": "Haley · Madanes · MRI",
        "category": "systemic",
        "founder": "Jay Haley / Cloe Madanes",
        "techniques": ["지시·과제", "역설적 개입", "재정의", "서열 탐색", "단기 목표"],
        "routing_keywords": ("전략적", "지시", "역설", "헤일리", "문제 유지", "단기가족"),
        "counselor_tone": "전략적이고 목표 지향적",
        "directive": (
            "전략적 가족치료처럼: 문제 유지 순환을 보고, 작지만 구체적인 지시·재정의로 "
            "변화를 유도하세요. 존중을 유지하며 권력·서열을 민감하게 다룹니다."
        ),
        "weight_profile": {"empathy": 0.5, "interpretation": 0.55, "structure": 0.85, "confrontation": 0.45},
    },
    ClinicalSchool.ATTACHMENT: {
        "label": "애착 이론 기반 상담",
        "short_label": "애착",
        "subtitle": "Bowlby · Ainsworth · Main",
        "category": "systemic",
        "founder": "John Bowlby / Mary Ainsworth",
        "techniques": ["애착 욕구 탐색", "안전기지", "정서 조율", "관계 수리", "내적작동모델"],
        "routing_keywords": ("애착", "버림", "안정", "불안애착", "회피애착", "안전기지", "조율"),
        "counselor_tone": "안전한 조율·연결",
        "directive": (
            "애착 관점으로: 연결·안전·조율 욕구를 중심으로 듣고, "
            "관계 수리와 안전기지 경험을 지지합니다. 애착 유형을 낙인처럼 쓰지 마세요."
        ),
        "weight_profile": {"empathy": 0.85, "interpretation": 0.55, "structure": 0.45, "confrontation": 0.2},
    },
    ClinicalSchool.EMDR_INFORMED: {
        "label": "EMDR 정보제공·안정화 안내",
        "short_label": "EMDR안내",
        "subtitle": "Francine Shapiro · 안정화·재처리 개념",
        "category": "brief_emotion",
        "founder": "Francine Shapiro",
        "techniques": ["안전장소", "안정화", "자원 설치 개념", "이중주의 안내", "전문가 의뢰"],
        "routing_keywords": ("EMDR", "외상재처리", "플래시백", "트리거", "양측자극", "재처리"),
        "counselor_tone": "신중한 안정화·의뢰",
        "directive": (
            "EMDR 자격 치료를 대체하지 않습니다. 안정화·안전장소·자원 개념만 교육적으로 안내하고, "
            "본격 재처리는 자격 전문가에게 의뢰하도록 안내하세요."
        ),
        "weight_profile": {"empathy": 0.8, "interpretation": 0.35, "structure": 0.7, "confrontation": 0.1},
    },
    ClinicalSchool.ART_THERAPY: {
        "label": "미술치료 · 예술적 표현",
        "short_label": "미술치료",
        "subtitle": "Naumburg · Kramer · Malchiodi",
        "category": "expressive",
        "founder": "Margaret Naumburg / Edith Kramer",
        "techniques": [
            "자유화",
            "낙서 기법(Scribble)",
            "만다라",
            "콜라주",
            "색채·감정",
            "과정 중심 제작",
            "작품 대화",
        ],
        "routing_keywords": (
            "미술", "그림", "그리기", "낙서", "만다라", "콜라주", "색", "미술치료",
            "말로 안", "표현이 어렵", "그림으로",
        ),
        "counselor_tone": "비판단적 창작·과정 존중",
        "directive": (
            "미술치료 가이드처럼: '잘 그리기'가 목표가 아님을 알리고, "
            "색·선·형태·과정 자체로 감정을 표현하도록 돕습니다. "
            "작품 해석을 단정하지 말고, 내담자의 의미를 함께 듣습니다. 의료 진단 금지."
        ),
        "weight_profile": {"empathy": 0.8, "interpretation": 0.35, "structure": 0.45, "confrontation": 0.15},
    },
    ClinicalSchool.MUSIC_THERAPY: {
        "label": "음악치료",
        "short_label": "음악치료",
        "subtitle": "Nordoff-Robbins · Bruscia",
        "category": "expressive",
        "founder": "Paul Nordoff / Clive Robbins / Kenneth Bruscia",
        "techniques": ["즉흥 연주", "노래 쓰기", "음악 감상 반응", "리듬 조율", "소리로 감정 표현"],
        "routing_keywords": ("음악", "노래", "리듬", "음악치료", "멜로디", "소리"),
        "counselor_tone": "리듬·소리로 조율",
        "directive": (
            "음악치료 안내처럼: 말 대신 리듬·선율·가사로 감정을 표현하도록 돕고, "
            "감상·즉흥의 느낌을 비판단적으로 나눕니다. 전문 음악치료를 대체하지 않습니다."
        ),
        "weight_profile": {"empathy": 0.8, "interpretation": 0.3, "structure": 0.45, "confrontation": 0.1},
    },
    ClinicalSchool.DANCE_MOVEMENT: {
        "label": "무용·동작치료",
        "short_label": "동작치료",
        "subtitle": "Marian Chace · Mary Whitehouse",
        "category": "expressive",
        "founder": "Marian Chace / Mary Whitehouse",
        "techniques": ["미러링", "즉흥 동작", "몸 인식", "동작 은유", "집단 리듬"],
        "routing_keywords": ("몸", "움직임", "무용", "동작", "댄스", "긴장", "몸으로"),
        "counselor_tone": "몸 감각·움직임 존중",
        "directive": (
            "동작치료 안내처럼: 말보다 몸 감각·작은 움직임으로 표현을 초대하고, "
            "안전·선택권을 강조합니다. 전문 무용치료를 대체하지 않습니다."
        ),
        "weight_profile": {"empathy": 0.8, "interpretation": 0.3, "structure": 0.4, "confrontation": 0.1},
    },
    ClinicalSchool.PLAY_THERAPY: {
        "label": "놀이치료",
        "short_label": "놀이치료",
        "subtitle": "Virginia Axline · Landreth",
        "category": "expressive",
        "founder": "Virginia Axline / Garry Landreth",
        "techniques": ["비지시적 놀이", "반영", "한계 설정", "상징 놀이", "선택권 존중"],
        "routing_keywords": ("놀이", "장난감", "아이처럼", "놀이치료", "상징놀이"),
        "counselor_tone": "수용적 놀이·반영",
        "directive": (
            "액슬라인·랜드레스 놀이치료처럼: 비판단적 반영과 선택권을 중심에 두고, "
            "상징 놀이를 통해 감정을 표현하도록 돕습니다. 아동 전문치료를 대체하지 않습니다."
        ),
        "weight_profile": {"empathy": 0.85, "interpretation": 0.35, "structure": 0.35, "confrontation": 0.1},
    },
    ClinicalSchool.SANDPLAY: {
        "label": "모래놀이치료",
        "short_label": "모래놀이",
        "subtitle": "Dora Kalff · Lowenfeld",
        "category": "expressive",
        "founder": "Dora Kalff / Margaret Lowenfeld",
        "techniques": ["모래상자 장면", "미니어처 상징", "침묵적 동행", "장면 관찰", "통합 이야기"],
        "routing_keywords": ("모래", "모래놀이", "상자", "미니어처", "샌드플레이"),
        "counselor_tone": "조용한 상징 동행",
        "directive": (
            "칼프 모래놀이 안내처럼: 해석을 서두르지 말고, 장면·상징을 내담자가 말하도록 "
            "침묵과 안전을 제공합니다. 전문 모래놀이치료를 대체하지 않습니다."
        ),
        "weight_profile": {"empathy": 0.8, "interpretation": 0.4, "structure": 0.35, "confrontation": 0.1},
    },
    ClinicalSchool.POSITIVE_PSYCHOLOGY: {
        "label": "긍정심리학",
        "short_label": "긍정심리",
        "subtitle": "Martin Seligman · Csikszentmihalyi",
        "category": "integrative",
        "founder": "Martin Seligman",
        "techniques": ["강점 탐색", "감사 일기", "흐름(flow)", "PERMA", "낙관성 연습"],
        "routing_keywords": ("강점", "감사", "행복", "긍정", "PERMA", "회복탄력성"),
        "counselor_tone": "강점·성장 지향",
        "directive": (
            "긍정심리 가이드처럼: 문제를 무시하지 않으면서도 강점·감사·의미를 균형 있게 탐색하세요. "
            "독성 긍정은 피합니다."
        ),
        "weight_profile": {"empathy": 0.7, "interpretation": 0.35, "structure": 0.55, "confrontation": 0.2},
    },
    ClinicalSchool.FEMINIST: {
        "label": "페미니스트 상담",
        "short_label": "페미니스트",
        "subtitle": "Brown · Enns · 권력·사회맥락",
        "category": "integrative",
        "founder": "Laura Brown / Carolyn Enns",
        "techniques": ["권력 분석", "사회맥락화", "임파워먼트", "평등 관계", "정체성 존중"],
        "routing_keywords": ("성역할", "차별", "권력", "페미", "억압", "평등", "가스라이팅"),
        "counselor_tone": "평등·임파워먼트",
        "directive": (
            "페미니스트 상담처럼: 개인 문제를 사회·권력 맥락과 연결해 이해하고, "
            "내담자의 목소리·선택·임파워먼트를 중심에 둡니다."
        ),
        "weight_profile": {"empathy": 0.75, "interpretation": 0.55, "structure": 0.5, "confrontation": 0.35},
    },
    ClinicalSchool.MULTICULTURAL: {
        "label": "다문화·교차성 상담",
        "short_label": "다문화",
        "subtitle": "Sue · Sue · 문화적 겸손",
        "category": "integrative",
        "founder": "Derald Wing Sue",
        "techniques": ["문화적 겸손", "세계관 탐색", "정체성 존중", "편견 인식", "맥락적 개입"],
        "routing_keywords": ("문화", "차별", "정체성", "이민", "편견", "다문화", "교차성"),
        "counselor_tone": "문화적으로 겸손한 경청",
        "directive": (
            "다문화 상담처럼: 문화적 겸손으로 세계관·정체성·차별 경험을 듣고, "
            "서구 중심 가정을 강요하지 않습니다."
        ),
        "weight_profile": {"empathy": 0.8, "interpretation": 0.45, "structure": 0.45, "confrontation": 0.25},
    },
}

from app.services.addiction_theories import ADDICTION_THEORIES, ADDICTION_USER_LABELS

EXTRA_USER_LABELS.update(ADDICTION_USER_LABELS)
EXTRA_THEORIES.update(ADDICTION_THEORIES)
