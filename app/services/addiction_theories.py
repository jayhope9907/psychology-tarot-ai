"""약물·행동 중독 관련 상담 이론·기법 카탈로그 (웰니스·교육용, 비의료).

임상 문헌( MI, RP, CRA/CRAFT, CM, Matrix, TSF, 해로 줄이기, SMART 등)을
**자기성찰·동기·습관 탐색 AI 가이드**로만 매핑합니다. 진단·처방·해독·의료 대체가 아닙니다.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.models.clinical import ClinicalSchool

ADDICTION_CATEGORY = "substance_addiction"

ADDICTION_USER_LABELS: Dict[ClinicalSchool, Dict[str, str]] = {
    ClinicalSchool.RELAPSE_PREVENTION: {
        "user_label": "재발예방 습관상담",
        "user_short_label": "재발예방",
    },
    ClinicalSchool.CONTINGENCY_MANAGEMENT: {
        "user_label": "보상·습관 상담",
        "user_short_label": "보상관리",
    },
    ClinicalSchool.CRA_COMMUNITY: {
        "user_label": "생활재구성 상담",
        "user_short_label": "CRA",
    },
    ClinicalSchool.CRAFT_FAMILY: {
        "user_label": "가족동기 상담",
        "user_short_label": "CRAFT",
    },
    ClinicalSchool.TWELVE_STEP_FACILITATION: {
        "user_label": "회복모임상담 안내",
        "user_short_label": "TSF안내",
    },
    ClinicalSchool.MATRIX_MODEL: {
        "user_label": "구조화 회복 상담",
        "user_short_label": "매트릭스",
    },
    ClinicalSchool.HARM_REDUCTION: {
        "user_label": "해로줄이기 상담",
        "user_short_label": "해로줄이기",
    },
    ClinicalSchool.SMART_RECOVERY: {
        "user_label": "자기관리 회복상담",
        "user_short_label": "SMART",
    },
    ClinicalSchool.ADDICTION_CBT: {
        "user_label": "중독 인지행동 상담",
        "user_short_label": "중독CBT",
    },
    ClinicalSchool.CRAVING_MINDFULNESS: {
        "user_label": "갈망 마음챙김 상담",
        "user_short_label": "갈망챙김",
    },
}

_LEGAL = (
    " 의료 진단·해독·처방·치료를 대체하지 않습니다. "
    "위기·의존이 심각하면 전문 중독치료기관·정신건강의학과·1332·1393 연계를 우선하세요."
)

ADDICTION_THEORIES: Dict[ClinicalSchool, Dict[str, Any]] = {
    ClinicalSchool.RELAPSE_PREVENTION: {
        "label": "재발예방 모형 · Relapse Prevention",
        "short_label": "재발예방",
        "subtitle": "Marlatt · Gordon · 고위험 상황·대처",
        "category": ADDICTION_CATEGORY,
        "founder": "G. Alan Marlatt / Judith Gordon",
        "techniques": [
            "고위험 상황 목록화",
            "갈망 surf",
            "대처기술 연습",
            "생활균형(lifestyle balance)",
            "일탈 효과 재구성",
            "재발 비상 계획",
        ],
        "routing_keywords": (
            "재발",
            "다시 마셨",
            "참았다가",
            "유혹",
            "고위험",
            "갈망",
            "끊었다가",
            "또 했어",
            "실패",
        ),
        "counselor_tone": "비난 없이 상황·대처를 구조화",
        "directive": (
            "Marlatt 재발예방 가이드처럼: 고위험 상황·갈망·대처 선택을 함께 그려 보고, "
            "한 번의 일탈을 '전면 실패'로 보지 않도록 인지 재구성을 돕습니다."
            + _LEGAL
        ),
        "weight_profile": {"empathy": 0.7, "interpretation": 0.55, "structure": 0.8, "confrontation": 0.25},
    },
    ClinicalSchool.CONTINGENCY_MANAGEMENT: {
        "label": "유관관리 · Contingency Management",
        "short_label": "유관관리",
        "subtitle": "Higgins · Petry · 목표 행동·보강",
        "category": ADDICTION_CATEGORY,
        "founder": "Stephen Higgins / Nancy Petry",
        "techniques": [
            "목표 행동 명확화",
            "즉시·빈번 보강",
            "단계적 보상",
            "기록·체크인",
            "대안 보상 설계",
        ],
        "routing_keywords": ("보상", "포인트", "목표 달성", "보강", "동기 유지", "체크인", "실천"),
        "counselor_tone": "구체 목표·작은 성취 강화",
        "directive": (
            "유관관리 원리로: 달성 가능한 작은 목표·자기보상·기록 루틴을 설계하되, "
            "처벌적 톤과 금전 강요는 피합니다."
            + _LEGAL
        ),
        "weight_profile": {"empathy": 0.55, "interpretation": 0.3, "structure": 0.85, "confrontation": 0.2},
    },
    ClinicalSchool.CRA_COMMUNITY: {
        "label": "지역사회 강화접근 · CRA",
        "short_label": "CRA",
        "subtitle": "Hunt · Azrin · Meyers · 소베르 강화 환경",
        "category": ADDICTION_CATEGORY,
        "founder": "Nathan Azrin / Robert Meyers",
        "techniques": [
            "행복 척도·목표",
            "기능분석",
            "의사소통 기술",
            "문제해결",
            "소베르 사회활동",
            "직업·여가 재구성",
        ],
        "routing_keywords": ("생활 패턴", "술 친구", "여가", "일자리", "루틴", "환경", "빠져나오"),
        "counselor_tone": "환경·관계 재구성 협력",
        "directive": (
            "CRA처럼: 물질 강화 대신 소베르한 활동·관계·일상을 늘리는 방향으로 "
            "기능분석과 구체 계획을 돕습니다."
            + _LEGAL
        ),
        "weight_profile": {"empathy": 0.65, "interpretation": 0.45, "structure": 0.8, "confrontation": 0.25},
    },
    ClinicalSchool.CRAFT_FAMILY: {
        "label": "지역사회강화·가족훈련 · CRAFT",
        "short_label": "CRAFT",
        "subtitle": "Meyers · Smith · 가족 동기·안전",
        "category": ADDICTION_CATEGORY,
        "founder": "Robert Meyers / Jane Ellen Smith",
        "techniques": [
            "긍정 강화 훈련",
            "부정 결과 자연 노출",
            "초대 커뮤니케이션",
            "자기 돌봄",
            "안전 계획",
            "치료 참여 초대",
        ],
        "routing_keywords": ("가족이 술", "남편 중독", "아내 담배", "아이를", "어떻게 말하", "가족 중독", "도와주고"),
        "counselor_tone": "가족 안전·비대립·동기 초대",
        "directive": (
            "CRAFT 정신으로: 비난·대립 대신 안전·자기돌봄·초대형 소통을 안내하고, "
            "가족이 전문가 상담으로 이어지도록 돕습니다."
            + _LEGAL
        ),
        "weight_profile": {"empathy": 0.8, "interpretation": 0.4, "structure": 0.7, "confrontation": 0.2},
    },
    ClinicalSchool.TWELVE_STEP_FACILITATION: {
        "label": "12단계 촉진 · TSF (안내)",
        "short_label": "TSF",
        "subtitle": "Project MATCH · AA/NA 연계 촉진",
        "category": ADDICTION_CATEGORY,
        "founder": "Joseph Nowinski / Project MATCH",
        "techniques": [
            "무력감 인정 탐색",
            "동료 회복 연결",
            "모임 초대",
            "스폰서 개념 안내",
            "영성·의미(선택)",
        ],
        "routing_keywords": ("AA", "NA", "12단계", "모임", "단주", "단약", "중독자 모임", "스폰서"),
        "counselor_tone": "존중하는 동료회복 안내",
        "directive": (
            "TSF 안내자처럼: 12단계·동료 모임을 강요하지 말고, 관심 있으면 지역 AA/NA·전문기관 "
            "정보를 연결합니다. 종교·영성은 선택 사항으로 둡니다."
            + _LEGAL
        ),
        "weight_profile": {"empathy": 0.75, "interpretation": 0.35, "structure": 0.55, "confrontation": 0.15},
    },
    ClinicalSchool.MATRIX_MODEL: {
        "label": "매트릭스 모델 · Matrix",
        "short_label": "매트릭스",
        "subtitle": "Rawson · 자극제 등 구조화 외래 모형",
        "category": ADDICTION_CATEGORY,
        "founder": "Richard Rawson / Matrix Institute",
        "techniques": [
            "주간 구조화 일정",
            "재발예방 세션",
            "가족 교육",
            "소변·체크인 은유(자기기록)",
            "사회지지",
            "CBT 과제",
        ],
        "routing_keywords": ("필로폰", "자극제", "코카인", "구조화", "재활", "프로그램", "외래"),
        "counselor_tone": "구조적이되 지지적",
        "directive": (
            "Matrix식 구조화로: 주간 루틴·지지망·재발예방 주제를 나누되, "
            "실제 재활 프로그램·의료는 전문기관을 안내합니다."
            + _LEGAL
        ),
        "weight_profile": {"empathy": 0.6, "interpretation": 0.4, "structure": 0.9, "confrontation": 0.25},
    },
    ClinicalSchool.HARM_REDUCTION: {
        "label": "해로 줄이기 · Harm Reduction",
        "short_label": "해로줄이기",
        "subtitle": "Marlatt · 실용적 위험 감소",
        "category": ADDICTION_CATEGORY,
        "founder": "G. Alan Marlatt / Harm Reduction tradition",
        "techniques": [
            "위험 서열화",
            "현실적 목표 협상",
            "안전한 사용 정보(비권장·비처방)",
            "과다복용 위험 인식",
            "점진적 감량",
            "존중 기반 관계",
        ],
        "routing_keywords": ("끊기 어려", "줄이고", "당장 금단", "위험", "과음", "해로", "안전하게"),
        "counselor_tone": "비판단·현실적 위험 감소",
        "directive": (
            "해로 줄이기 정신으로: 완전 금단만이 '성공'이 아님을 존중하고, "
            "현실적 위험 감소·안전·전문 연계를 우선합니다. 사용을 권장하지 않습니다."
            + _LEGAL
        ),
        "weight_profile": {"empathy": 0.85, "interpretation": 0.35, "structure": 0.55, "confrontation": 0.1},
    },
    ClinicalSchool.SMART_RECOVERY: {
        "label": "SMART Recovery 도구 안내",
        "short_label": "SMART",
        "subtitle": "4-Point · CBT·REBT 기반 자기관리",
        "category": ADDICTION_CATEGORY,
        "founder": "SMART Recovery community",
        "techniques": [
            "동기 구축",
            "갈망 다루기",
            "생각·행동·감정(ABC)",
            "균형 잡힌 삶",
            "비용·이득 분석",
            "DISARM",
        ],
        "routing_keywords": ("SMART", "자기관리", "이성적으로", "도구", "셀프헬프", "단주 도구"),
        "counselor_tone": "도구 중심·자율성 존중",
        "directive": (
            "SMART 4포인트처럼: 동기·갈망·사고·삶의 균형을 도구로 탐색하고, "
            "자기효능감을 키웁니다."
            + _LEGAL
        ),
        "weight_profile": {"empathy": 0.6, "interpretation": 0.5, "structure": 0.75, "confrontation": 0.3},
    },
    ClinicalSchool.ADDICTION_CBT: {
        "label": "중독 인지행동치료 · CBT for SUD",
        "short_label": "중독CBT",
        "subtitle": "Carroll · 인지·행동·대처기술",
        "category": ADDICTION_CATEGORY,
        "founder": "Kathleen Carroll / Bruce Liese",
        "techniques": [
            "기능분석",
            "인지 왜곡 점검",
            "거절 기술",
            "문제해결",
            "활동 스케줄",
            "갈망 기록",
        ],
        "routing_keywords": (
            "술",
            "담배",
            "마약",
            "대마",
            "히로뽕",
            "약물",
            "중독",
            "의존",
            "금단",
            "해독",
            "rehab",
        ),
        "counselor_tone": "구조적 인지·행동 연습",
        "directive": (
            "중독 CBT처럼: 유발상황→생각→갈망→사용→결과 사슬을 함께 그리고, "
            "구체 대처·거절·대체행동을 한 가지만 연습합니다."
            + _LEGAL
        ),
        "weight_profile": {"empathy": 0.55, "interpretation": 0.55, "structure": 0.85, "confrontation": 0.35},
    },
    ClinicalSchool.CRAVING_MINDFULNESS: {
        "label": "갈망 마음챙김 · MBRP",
        "short_label": "갈망챙김",
        "subtitle": "Bowen · Chawla · Marlatt · MBRP",
        "category": ADDICTION_CATEGORY,
        "founder": "Sarah Bowen / Neha Chawla / G. Alan Marlatt",
        "techniques": [
            "urge surfing",
            "몸 감각 관찰",
            "자동 조종 알아차림",
            "호흡 앵커",
            "자기자비",
            "트리거 마음챙김",
        ],
        "routing_keywords": ("참을 수 없", "몸이 원", "손이 가", "갈망", "충동", "surfing", "마음챙김 중독"),
        "counselor_tone": "차분한 감각 관찰",
        "directive": (
            "MBRP처럼: 갈망을 '타야 할 파도'로 관찰하고, 몸 감각·호흡으로 충동과 행동을 분리합니다."
            + _LEGAL
        ),
        "weight_profile": {"empathy": 0.75, "interpretation": 0.3, "structure": 0.7, "confrontation": 0.1},
    },
}


# Technique ontology for corpus API / patent-style knowledge layer
ADDICTION_TECHNIQUE_ONTOLOGY: List[Dict[str, Any]] = [
    {
        "id": "oars",
        "name_ko": "OARS 동기대화",
        "schools": ["MOTIVATIONAL"],
        "phase": "engagement",
        "steps": ["개방형 질문", "긍정", "반영", "요약"],
    },
    {
        "id": "functional_analysis",
        "name_ko": "기능분석(ABC·사슬)",
        "schools": ["ADDICTION_CBT", "CRA_COMMUNITY", "RELAPSE_PREVENTION"],
        "phase": "assessment",
        "steps": ["선행사건", "생각·감정", "행동", "단기·장기 결과"],
    },
    {
        "id": "urge_surfing",
        "name_ko": "갈망 파도타기",
        "schools": ["CRAVING_MINDFULNESS", "RELAPSE_PREVENTION"],
        "phase": "coping",
        "steps": ["감각 알아차림", "고조 관찰", "감소 대기", "행동 선택"],
    },
    {
        "id": "high_risk_map",
        "name_ko": "고위험 상황 지도",
        "schools": ["RELAPSE_PREVENTION", "MATRIX_MODEL"],
        "phase": "prevention",
        "steps": ["사람", "장소", "감정", "시간대", "대처카드"],
    },
    {
        "id": "decisional_balance",
        "name_ko": "결정균형(비용·이득)",
        "schools": ["MOTIVATIONAL", "SMART_RECOVERY", "HARM_REDUCTION"],
        "phase": "motivation",
        "steps": ["유지 이득", "유지 비용", "변화 이득", "변화 비용"],
    },
    {
        "id": "refusal_skills",
        "name_ko": "거절 기술",
        "schools": ["ADDICTION_CBT", "CRA_COMMUNITY"],
        "phase": "skills",
        "steps": ["분명한 거절", "대체 제안", "자리 떠나기", "지지자 연락"],
    },
    {
        "id": "sobriety_sampling",
        "name_ko": "단약·단주 샘플링",
        "schools": ["CRA_COMMUNITY", "HARM_REDUCTION"],
        "phase": "experiment",
        "steps": ["짧은 목표기간", "기록", "어려움 점검", "전문연계 판단"],
    },
    {
        "id": "family_positive_reinforce",
        "name_ko": "가족 긍정강화",
        "schools": ["CRAFT_FAMILY"],
        "phase": "family",
        "steps": ["소베르 행동 관찰", "구체 칭찬", "자기돌봄", "안전계획"],
    },
    {
        "id": "recovery_network",
        "name_ko": "회복 지지망 연결",
        "schools": ["TWELVE_STEP_FACILITATION", "MATRIX_MODEL", "CRA_COMMUNITY"],
        "phase": "support",
        "steps": ["모임/기관 정보", "첫 방문 계획", "연락처", "위기번호"],
    },
    {
        "id": "crisis_substance_handoff",
        "name_ko": "중독·위기 전문연계",
        "schools": ["HARM_REDUCTION", "ADDICTION_CBT", "MOTIVATIONAL"],
        "phase": "safety",
        "steps": ["위험평가", "1332·1393·119", "응급실/중독센터", "혼자가 아님 알림"],
    },
]


def addiction_corpus() -> Dict[str, Any]:
    return {
        "corpus_id": "substance-addiction-wellness-v1",
        "disclaimer": (
            "교육·자기성찰용 이론·기법 목록입니다. "
            "약물중독의 의료적 치료·해독·처방을 제공하지 않으며, "
            "임상 현장에서는 면허 전문가의 판단이 우선합니다."
        ),
        "category": ADDICTION_CATEGORY,
        "category_label": "약물·행동 중독 · 회복 지원",
        "theory_count": len(ADDICTION_THEORIES),
        "technique_count": len(ADDICTION_TECHNIQUE_ONTOLOGY),
        "theories": [
            {
                "school": school.value,
                "label": meta["label"],
                "short_label": meta["short_label"],
                "founder": meta["founder"],
                "techniques": meta["techniques"],
                "keywords": list(meta["routing_keywords"]),
            }
            for school, meta in ADDICTION_THEORIES.items()
        ],
        "techniques": ADDICTION_TECHNIQUE_ONTOLOGY,
        "clinical_handoff": [
            {"label": "중독상담전화", "tel": "1332"},
            {"label": "자살예방", "tel": "1393"},
            {"label": "응급", "tel": "119"},
            {"label": "보건복지상담", "tel": "129"},
        ],
    }
