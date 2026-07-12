"""상담심리학·표현예술치료 주요 학자 카탈로그."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models.clinical import ClinicalSchool

SCHOLARS: List[Dict[str, Any]] = [
    # Humanistic / existential
    {"id": "rogers", "name": "Carl Rogers", "name_ko": "칼 로저스", "school": "ROGERIAN", "era": "1902–1987", "focus": "인간중심 · 공감·수용", "techniques": ["감정 반영", "무조건적 존중", "일치성"], "works": ["Client-Centered Therapy"]},
    {"id": "perls", "name": "Fritz Perls", "name_ko": "프리츠 펄스", "school": "GESTALT", "era": "1893–1970", "focus": "게슈탈트 · 빈 의자", "techniques": ["빈 의자", "지금-여기", "역할 바꾸기"], "works": ["Gestalt Therapy"]},
    {"id": "laura_perls", "name": "Laura Perls", "name_ko": "로라 펄스", "school": "GESTALT", "era": "1905–1990", "focus": "게슈탈트 · 접촉 경계", "techniques": ["접촉", "지지와 도전"], "works": ["Living at the Boundary"]},
    {"id": "may", "name": "Rollo May", "name_ko": "롤로 메이", "school": "EXISTENTIAL", "era": "1909–1994", "focus": "실존 · 불안·자유", "techniques": ["실존 주제", "자유·책임"], "works": ["The Meaning of Anxiety"]},
    {"id": "yalom", "name": "Irvin Yalom", "name_ko": "어빈 얄롬", "school": "EXISTENTIAL", "era": "1931–", "focus": "실존 · 집단·죽음·고립", "techniques": ["여기-지금", "실존 요인"], "works": ["Existential Psychotherapy"]},
    {"id": "frankl", "name": "Viktor Frankl", "name_ko": "빅터 프랑클", "school": "LOGOTHERAPY", "era": "1905–1997", "focus": "의미치료", "techniques": ["의미 탐색", "역설의도"], "works": ["Man's Search for Meaning"]},
    # CBT family
    {"id": "beck", "name": "Aaron T. Beck", "name_ko": "아론 벡", "school": "BECK_CBT", "era": "1921–2021", "focus": "인지치료", "techniques": ["자동적 사고", "인지 재구조화"], "works": ["Cognitive Therapy and the Emotional Disorders"]},
    {"id": "j_beck", "name": "Judith S. Beck", "name_ko": "주디스 벡", "school": "BECK_CBT", "era": "1954–", "focus": "CBT 임상·교육", "techniques": ["사례개념화", "숙제"], "works": ["Cognitive Behavior Therapy: Basics and Beyond"]},
    {"id": "ellis", "name": "Albert Ellis", "name_ko": "알버트 엘리스", "school": "REBT", "era": "1913–2007", "focus": "REBT", "techniques": ["ABC", "논박"], "works": ["Reason and Emotion in Psychotherapy"]},
    {"id": "glasser", "name": "William Glasser", "name_ko": "윌리엄 글래서", "school": "REALITY_THERAPY", "era": "1925–2013", "focus": "현실치료 · 선택이론", "techniques": ["WDEP", "선택"], "works": ["Reality Therapy"]},
    {"id": "linehan", "name": "Marsha Linehan", "name_ko": "마샤 리네한", "school": "DBT", "era": "1943–", "focus": "DBT", "techniques": ["마음챙김", "고통감내", "감정조절"], "works": ["Cognitive-Behavioral Treatment of Borderline Personality Disorder"]},
    {"id": "hayes", "name": "Steven C. Hayes", "name_ko": "스티븐 헤이스", "school": "ACT", "era": "1948–", "focus": "수용전념치료", "techniques": ["수용", "탈융합", "가치"], "works": ["Get Out of Your Mind and Into Your Life"]},
    {"id": "young", "name": "Jeffrey Young", "name_ko": "제프리 영", "school": "SCHEMA_THERAPY", "era": "1950–", "focus": "스키마 치료", "techniques": ["스키마", "모드", "재양육"], "works": ["Schema Therapy"]},
    {"id": "segal", "name": "Zindel Segal", "name_ko": "진델 시걸", "school": "MBCT", "era": "1956–", "focus": "MBCT", "techniques": ["몸 스캔", "호흡공간"], "works": ["Mindfulness-Based Cognitive Therapy for Depression"]},
    {"id": "williams_mbct", "name": "Mark Williams", "name_ko": "마크 윌리엄스", "school": "MBCT", "era": "1952–", "focus": "MBCT", "techniques": ["마음챙김", "재발예방"], "works": ["The Mindful Way through Depression"]},
    {"id": "teasdale", "name": "John Teasdale", "name_ko": "존 티즈데일", "school": "MBCT", "era": "1944–", "focus": "MBCT", "techniques": ["탈동일시", "마음챙김"], "works": ["Mindfulness-Based Cognitive Therapy"]},
    {"id": "gilbert", "name": "Paul Gilbert", "name_ko": "폴 길버트", "school": "CFT", "era": "1951–", "focus": "연민중심치료", "techniques": ["자기자비", "안정화"], "works": ["The Compassionate Mind"]},
    # Psychodynamic
    {"id": "freud", "name": "Sigmund Freud", "name_ko": "지그문트 프로이트", "school": "FREUDIAN", "era": "1856–1939", "focus": "정신분석", "techniques": ["자유연상", "방어", "전이"], "works": ["The Interpretation of Dreams"]},
    {"id": "adler", "name": "Alfred Adler", "name_ko": "알프레드 아들러", "school": "ADLERIAN", "era": "1870–1937", "focus": "개별심리", "techniques": ["생활양식", "용기", "사회적 관심"], "works": ["Understanding Human Nature"]},
    {"id": "jung", "name": "Carl Gustav Jung", "name_ko": "칼 구스타프 융", "school": "JUNGIAN", "era": "1875–1961", "focus": "분석심리 · 상징", "techniques": ["꿈 분석", "원형", "개성화"], "works": ["Man and His Symbols"]},
    {"id": "klein", "name": "Melanie Klein", "name_ko": "멜라니 클라인", "school": "OBJECT_RELATIONS", "era": "1882–1960", "focus": "대상관계", "techniques": ["투사적 동일시", "놀이 관찰"], "works": ["Envy and Gratitude"]},
    {"id": "winnicott", "name": "D.W. Winnicott", "name_ko": "도널드 위니콧", "school": "OBJECT_RELATIONS", "era": "1896–1971", "focus": "홀딩·중간대상", "techniques": ["홀딩 환경", "중간대상"], "works": ["Playing and Reality"]},
    {"id": "kohut", "name": "Heinz Kohut", "name_ko": "하인츠 코헛", "school": "SELF_PSYCHOLOGY", "era": "1913–1981", "focus": "자기심리학", "techniques": ["공감적 몰입", "자기대상"], "works": ["The Analysis of the Self"]},
    {"id": "berne", "name": "Eric Berne", "name_ko": "에릭 번", "school": "TRANSACTIONAL_ANALYSIS", "era": "1910–1970", "focus": "교류분석", "techniques": ["P-A-C", "게임", "각본"], "works": ["Games People Play"]},
    # Systemic / relational
    {"id": "white", "name": "Michael White", "name_ko": "마이클 화이트", "school": "NARRATIVE", "era": "1948–2008", "focus": "이야기치료", "techniques": ["외화", "독특한 결과"], "works": ["Maps of Narrative Practice"]},
    {"id": "epston", "name": "David Epston", "name_ko": "데이비드 엡스톤", "school": "NARRATIVE", "era": "1944–", "focus": "이야기치료", "techniques": ["편지", "외화"], "works": ["Narrative Means to Therapeutic Ends"]},
    {"id": "klerman", "name": "Gerald Klerman", "name_ko": "제럴드 클레르만", "school": "IPT", "era": "1928–1992", "focus": "대인관계치료", "techniques": ["역할 전환", "대인 갈등"], "works": ["Interpersonal Psychotherapy of Depression"]},
    {"id": "weissman", "name": "Myrna Weissman", "name_ko": "머나 와이즈만", "school": "IPT", "era": "1935–", "focus": "IPT", "techniques": ["애도", "대인 결핍"], "works": ["Comprehensive Guide to Interpersonal Psychotherapy"]},
    {"id": "bowen", "name": "Murray Bowen", "name_ko": "머레이 보웬", "school": "BOWEN_SYSTEMS", "era": "1913–1990", "focus": "가족체계", "techniques": ["분화", "삼각관계", "가계도"], "works": ["Family Therapy in Clinical Practice"]},
    {"id": "minuchin", "name": "Salvador Minuchin", "name_ko": "살바도르 미누친", "school": "STRUCTURAL_FAMILY", "era": "1921–2017", "focus": "구조적 가족치료", "techniques": ["경계", "재구조화"], "works": ["Families and Family Therapy"]},
    {"id": "satir", "name": "Virginia Satir", "name_ko": "버지니아 사티어", "school": "SATIR", "era": "1916–1988", "focus": "경험적 가족치료", "techniques": ["의사소통 자세", "가족 조각"], "works": ["Peoplemaking"]},
    {"id": "haley", "name": "Jay Haley", "name_ko": "제이 헤일리", "school": "STRATEGIC_FAMILY", "era": "1923–2007", "focus": "전략적 가족치료", "techniques": ["지시", "역설"], "works": ["Problem-Solving Therapy"]},
    {"id": "madanes", "name": "Cloe Madanes", "name_ko": "클로에 마다네스", "school": "STRATEGIC_FAMILY", "era": "1940–", "focus": "전략적 가족", "techniques": ["전략", "유머"], "works": ["Strategic Family Therapy"]},
    {"id": "bowlby", "name": "John Bowlby", "name_ko": "존 볼비", "school": "ATTACHMENT", "era": "1907–1990", "focus": "애착 이론", "techniques": ["안전기지", "내적작동모델"], "works": ["Attachment and Loss"]},
    {"id": "ainsworth", "name": "Mary Ainsworth", "name_ko": "메리 애인스워스", "school": "ATTACHMENT", "era": "1913–1999", "focus": "애착 유형", "techniques": ["낯선 상황", "애착 유형"], "works": ["Patterns of Attachment"]},
    {"id": "johnson", "name": "Sue Johnson", "name_ko": "수 존슨", "school": "EFT", "era": "1947–", "focus": "감정중심치료(EFT)", "techniques": ["애착 정서", "순환 재구성"], "works": ["Hold Me Tight"]},
    {"id": "greenberg", "name": "Leslie Greenberg", "name_ko": "레슬리 그린버그", "school": "EFT", "era": "1945–", "focus": "감정중심치료", "techniques": ["감정 각성", "정서 변형"], "works": ["Emotion-Focused Therapy"]},
    # Brief / trauma
    {"id": "de_shazer", "name": "Steve de Shazer", "name_ko": "스티브 드 셰이저", "school": "SOLUTION_FOCUSED", "era": "1940–2005", "focus": "해결중심", "techniques": ["기적 질문", "예외"], "works": ["Keys to Solution in Brief Therapy"]},
    {"id": "berg", "name": "Insoo Kim Berg", "name_ko": "인수 킴 버그", "school": "SOLUTION_FOCUSED", "era": "1934–2007", "focus": "해결중심", "techniques": ["스케일링", "칭찬"], "works": ["Interviewing for Solutions"]},
    {"id": "miller_mi", "name": "William R. Miller", "name_ko": "윌리엄 밀러", "school": "MOTIVATIONAL", "era": "1947–", "focus": "동기강화상담", "techniques": ["OARS", "변화대화"], "works": ["Motivational Interviewing"]},
    {"id": "rollnick", "name": "Stephen Rollnick", "name_ko": "스티븐 롤닉", "school": "MOTIVATIONAL", "era": "1952–", "focus": "MI", "techniques": ["양가성", "협력"], "works": ["Motivational Interviewing"]},
    {"id": "herman", "name": "Judith Herman", "name_ko": "주디스 허먼", "school": "TRAUMA_INFORMED", "era": "1942–", "focus": "외상 · 회복 단계", "techniques": ["안전", "애도", "재연결"], "works": ["Trauma and Recovery"]},
    {"id": "van_der_kolk", "name": "Bessel van der Kolk", "name_ko": "베셀 반 데어 콜크", "school": "TRAUMA_INFORMED", "era": "1943–", "focus": "몸·외상", "techniques": ["몸 기반", "안전"], "works": ["The Body Keeps the Score"]},
    {"id": "shapiro", "name": "Francine Shapiro", "name_ko": "프랜신 샤피로", "school": "EMDR_INFORMED", "era": "1948–2019", "focus": "EMDR", "techniques": ["안정화", "재처리 개념"], "works": ["Eye Movement Desensitization and Reprocessing"]},
    # Expressive / arts
    {"id": "moreno", "name": "Jacob L. Moreno", "name_ko": "제이콥 모레노", "school": "PSYCHODRAMA", "era": "1889–1974", "focus": "사이코드라마", "techniques": ["역할극", "더블링", "미러링"], "works": ["Who Shall Survive?"]},
    {"id": "zerka_moreno", "name": "Zerka T. Moreno", "name_ko": "저카 모레노", "school": "PSYCHODRAMA", "era": "1917–2016", "focus": "사이코드라마", "techniques": ["보조자아", "장면"], "works": ["Psychodrama, Surplus Reality and the Art of Healing"]},
    {"id": "emunah", "name": "Renee Emunah", "name_ko": "르네 에무나", "school": "DRAMA_THERAPY", "era": "현대", "focus": "연극치료", "techniques": ["과정 드라마", "거리두기"], "works": ["Acting for Real"]},
    {"id": "jones", "name": "Phil Jones", "name_ko": "필 존스", "school": "DRAMA_THERAPY", "era": "현대", "focus": "드라마 테라피", "techniques": ["상징", "몸", "스토리"], "works": ["Drama as Therapy"]},
    {"id": "naumburg", "name": "Margaret Naumburg", "name_ko": "마거릿 나움버그", "school": "ART_THERAPY", "era": "1890–1983", "focus": "역동적 미술치료", "techniques": ["자유화", "상징 연상", "작품 대화"], "works": ["Dynamically Oriented Art Therapy"]},
    {"id": "kramer", "name": "Edith Kramer", "name_ko": "에디트 크래머", "school": "ART_THERAPY", "era": "1916–2014", "focus": "미술치료 · 승화", "techniques": ["과정 중심 제작", "승화", "예술적 완성"], "works": ["Art as Therapy with Children"]},
    {"id": "cane", "name": "Florence Cane", "name_ko": "플로렌스 케인", "school": "ART_THERAPY", "era": "1882–1952", "focus": "낙서·움직임 미술", "techniques": ["낙서 기법", "몸·선"], "works": ["The Artist in Each of Us"]},
    {"id": "kwiatkowska", "name": "Hanna Yaxa Kwiatkowska", "name_ko": "한나 크비아트코프스카", "school": "ART_THERAPY", "era": "현대", "focus": "가족 미술치료", "techniques": ["가족 합동작품", "가족 평가"], "works": ["Family Therapy and Evaluation through Art"]},
    {"id": "ulman", "name": "Elinor Ulman", "name_ko": "엘리너 울만", "school": "ART_THERAPY", "era": "1910–1991", "focus": "미술치료 평가", "techniques": ["Ulman 평가", "진단적 미술"], "works": ["Art Therapy in Theory and Practice"]},
    {"id": "rubin", "name": "Judith Aron Rubin", "name_ko": "주디스 루빈", "school": "ART_THERAPY", "era": "현대", "focus": "아동·임상 미술치료", "techniques": ["발달적 미술", "매체 탐색"], "works": ["Child Art Therapy", "Approaches to Art Therapy"]},
    {"id": "malchiodi", "name": "Cathy A. Malchiodi", "name_ko": "캐시 말키오디", "school": "ART_THERAPY", "era": "현대", "focus": "트라우마·표현예술", "techniques": ["트라우마 정보 미술", "감각 기반"], "works": ["The Handbook of Art Therapy"]},
    {"id": "mcniff", "name": "Shaun McNiff", "name_ko": "숀 맥니프", "school": "ART_THERAPY", "era": "현대", "focus": "예술기반 연구·치유", "techniques": ["예술로서의 치료", "스튜디오"], "works": ["Art as Medicine"]},
    {"id": "hinz", "name": "Lisa D. Hinz", "name_ko": "리사 힌츠", "school": "ART_THERAPY", "era": "현대", "focus": "표현치료 연속체(ETC)", "techniques": ["ETC", "매체 속성"], "works": ["Expressive Therapies Continuum"]},
    {"id": "landgarten", "name": "Helen Landgarten", "name_ko": "헬렌 랜드가르텐", "school": "ART_THERAPY", "era": "현대", "focus": "임상 미술치료", "techniques": ["콜라주", "가족 미술"], "works": ["Clinical Art Therapy"]},
    {"id": "wadeson", "name": "Harriet Wadeson", "name_ko": "해리엇 웨이드슨", "school": "ART_THERAPY", "era": "현대", "focus": "미술치료 연구·교육", "techniques": ["집단 미술", "연구"], "works": ["Art Psychotherapy"]},
    {"id": "nordoff", "name": "Paul Nordoff", "name_ko": "폴 노드오프", "school": "MUSIC_THERAPY", "era": "1909–1977", "focus": "창조적 음악치료", "techniques": ["즉흥 연주", "공동 창조"], "works": ["Creative Music Therapy"]},
    {"id": "robbins_music", "name": "Clive Robbins", "name_ko": "클라이브 로빈스", "school": "MUSIC_THERAPY", "era": "1927–2011", "focus": "Nordoff-Robbins", "techniques": ["즉흥", "관계 음악"], "works": ["Creative Music Therapy"]},
    {"id": "bruscia", "name": "Kenneth Bruscia", "name_ko": "케네스 브루스시아", "school": "MUSIC_THERAPY", "era": "현대", "focus": "음악치료 정의·방법", "techniques": ["감상", "재창조", "즉흥", "작곡"], "works": ["Defining Music Therapy"]},
    {"id": "chace", "name": "Marian Chace", "name_ko": "매리언 체이스", "school": "DANCE_MOVEMENT", "era": "1896–1970", "focus": "무용·동작치료", "techniques": ["미러링", "집단 리듬"], "works": ["Dance Therapy Foundations"]},
    {"id": "whitehouse", "name": "Mary Starks Whitehouse", "name_ko": "메리 화이트하우스", "school": "DANCE_MOVEMENT", "era": "1911–1979", "focus": "Authentic Movement", "techniques": ["진정한 움직임", "목격자"], "works": ["Authentic Movement"]},
    {"id": "axline", "name": "Virginia Axline", "name_ko": "버지니아 액슬라인", "school": "PLAY_THERAPY", "era": "1911–1988", "focus": "비지시적 놀이치료", "techniques": ["반영", "수용", "한계"], "works": ["Dibs in Search of Self", "Play Therapy"]},
    {"id": "landreth", "name": "Garry Landreth", "name_ko": "개리 랜드레스", "school": "PLAY_THERAPY", "era": "현대", "focus": "아동중심 놀이치료", "techniques": ["비지시", "치료적 한계"], "works": ["Play Therapy: The Art of the Relationship"]},
    {"id": "kalff", "name": "Dora Kalff", "name_ko": "도라 칼프", "school": "SANDPLAY", "era": "1904–1990", "focus": "모래놀이치료", "techniques": ["모래상자", "상징", "자유·보호 공간"], "works": ["Sandplay: A Psychotherapeutic Approach to the Psyche"]},
    {"id": "lowenfeld", "name": "Margaret Lowenfeld", "name_ko": "마거릿 로웬펠트", "school": "SANDPLAY", "era": "1890–1973", "focus": "세계기법", "techniques": ["World Technique", "미니어처"], "works": ["Play in Childhood"]},
    # Integrative / contextual
    {"id": "kabat_zinn", "name": "Jon Kabat-Zinn", "name_ko": "존 카밧진", "school": "MINDFULNESS", "era": "1944–", "focus": "MBSR", "techniques": ["호흡", "몸 스캔", "비판단"], "works": ["Full Catastrophe Living"]},
    {"id": "seligman", "name": "Martin Seligman", "name_ko": "마틴 셀리그먼", "school": "POSITIVE_PSYCHOLOGY", "era": "1942–", "focus": "긍정심리학", "techniques": ["강점", "PERMA"], "works": ["Flourish"]},
    {"id": "csikszentmihalyi", "name": "Mihaly Csikszentmihalyi", "name_ko": "미하이 칙센트미하이", "school": "POSITIVE_PSYCHOLOGY", "era": "1934–2021", "focus": "몰입(flow)", "techniques": ["흐름", "최적 경험"], "works": ["Flow"]},
    {"id": "brown_laura", "name": "Laura S. Brown", "name_ko": "로라 브라운", "school": "FEMINIST", "era": "현대", "focus": "페미니스트 치료", "techniques": ["권력 분석", "임파워먼트"], "works": ["Feminist Therapy"]},
    {"id": "enns", "name": "Carolyn Zerbe Enns", "name_ko": "캐롤린 엔스", "school": "FEMINIST", "era": "현대", "focus": "페미니스트 상담심리", "techniques": ["성역할", "사회맥락"], "works": ["Feminist Theories and Feminist Psychotherapies"]},
    {"id": "sue", "name": "Derald Wing Sue", "name_ko": "더럴드 윙 수", "school": "MULTICULTURAL", "era": "현대", "focus": "다문화 상담", "techniques": ["문화적 겸손", "마이크로어그레션"], "works": ["Counseling the Culturally Diverse"]},
    {"id": "norcross", "name": "John C. Norcross", "name_ko": "존 노크로스", "school": "INTEGRATIVE", "era": "현대", "focus": "통합·공통요인", "techniques": ["치료 관계", "맞춤 매칭"], "works": ["Psychotherapy Relationships That Work"]},
    {"id": "prochaska", "name": "James Prochaska", "name_ko": "제임스 프로차스카", "school": "INTEGRATIVE", "era": "현대", "focus": "변화 단계 모형", "techniques": ["단계별 개입", "과정"], "works": ["Changing for Good"]},
]

ART_THERAPY_TECHNIQUES: List[Dict[str, Any]] = [
    {"id": "free_drawing", "name": "자유화", "name_en": "Free drawing", "scholars": ["naumburg", "kramer"], "blurb": "주제 없이 선·색·형태로 지금 마음을 남기기"},
    {"id": "scribble", "name": "낙서 기법", "name_en": "Scribble technique", "scholars": ["cane", "naumburg"], "blurb": "눈을 감고 낙서한 뒤, 보이는 형태·감정을 발견하기"},
    {"id": "mandala", "name": "만다라", "name_en": "Mandala", "scholars": ["jung", "malchiodi"], "blurb": "원 안에 색·무늬로 중심·경계를 느껴보기"},
    {"id": "collage", "name": "콜라주", "name_en": "Collage", "scholars": ["landgarten", "malchiodi"], "blurb": "이미지·조각을 모아 ‘지금의 나’ 장면 만들기"},
    {"id": "color_emotion", "name": "색채·감정", "name_en": "Color & emotion", "scholars": ["kramer", "hinz"], "blurb": "말로 대신할 색을 고르고 넓이·배치로 세기 표현"},
    {"id": "process_art", "name": "과정 중심 제작", "name_en": "Process-oriented art", "scholars": ["kramer", "mcniff"], "blurb": "완성도보다 만드는 순간의 감각·선택에 머무르기"},
    {"id": "family_art", "name": "가족 미술", "name_en": "Family art therapy", "scholars": ["kwiatkowska", "landgarten"], "blurb": "관계·역할을 그림·합동작품으로 살펴보기"},
    {"id": "trauma_informed_art", "name": "트라우마 정보 미술", "name_en": "Trauma-informed art", "scholars": ["malchiodi"], "blurb": "안전·선택권·감각 조절을 우선한 표현"},
    {"id": "etc_media", "name": "표현치료 연속체(ETC)", "name_en": "Expressive Therapies Continuum", "scholars": ["hinz"], "blurb": "감각·감정·인지·상징 층위에 맞는 매체 고르기"},
    {"id": "artwork_dialogue", "name": "작품 대화", "name_en": "Artwork dialogue", "scholars": ["naumburg", "rubin"], "blurb": "작품이 ‘말한다면’ — 제목·한 문장·감정을 남기기"},
]


def list_scholars(
    school: Optional[str] = None,
    query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = (query or "").strip().lower()
    items: List[Dict[str, Any]] = []
    for s in SCHOLARS:
        if school and s["school"] != school:
            continue
        if q:
            blob = " ".join(
                [
                    s["name"],
                    s["name_ko"],
                    s["school"],
                    s["focus"],
                    " ".join(s.get("techniques") or []),
                ]
            ).lower()
            if q not in blob:
                continue
        school_ok = s["school"] in {x.value for x in ClinicalSchool}
        items.append({**s, "school_valid": school_ok})
    return items


def list_art_techniques() -> List[Dict[str, Any]]:
    scholar_map = {s["id"]: s for s in SCHOLARS}
    rows = []
    for tech in ART_THERAPY_TECHNIQUES:
        linked = [scholar_map[i] for i in tech["scholars"] if i in scholar_map]
        rows.append(
            {
                **tech,
                "scholar_details": [
                    {"id": x["id"], "name": x["name"], "name_ko": x["name_ko"]} for x in linked
                ],
            }
        )
    return rows


def scholars_corpus() -> Dict[str, Any]:
    by_school: Dict[str, int] = {}
    for s in SCHOLARS:
        by_school[s["school"]] = by_school.get(s["school"], 0) + 1
    return {
        "title": "상담심리학 · 표현예술치료 학자",
        "disclaimer": (
            "교육·자기성찰용 참고 목록입니다. 특정 학파의 정식 자격·면허 치료를 대체하지 않습니다."
        ),
        "scholar_count": len(SCHOLARS),
        "art_technique_count": len(ART_THERAPY_TECHNIQUES),
        "schools_covered": len(by_school),
        "by_school": by_school,
        "scholars": list_scholars(),
        "art_techniques": list_art_techniques(),
    }
