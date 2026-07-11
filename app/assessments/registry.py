from __future__ import annotations

from typing import Any, Dict, List

# 심리학파·검사 영역 taxonomy
ASSESSMENT_DOMAINS: Dict[str, Dict[str, Any]] = {
    "clinical_mood": {
        "label": "임상 정서 (우울)",
        "school": "정신의학·DSM 스크리닝",
        "instruments": ["phq9"],
    },
    "clinical_anxiety": {
        "label": "임상 불안",
        "school": "정신의학·DSM 스크리닝",
        "instruments": ["gad7"],
    },
    "clinical_sleep": {
        "label": "수면",
        "school": "임상 증상",
        "instruments": ["isi"],
    },
    "clinical_stress": {
        "label": "스트레스",
        "school": "임상 증상",
        "instruments": ["pss"],
    },
    "clinical_trauma": {
        "label": "외상 스트레스",
        "school": "정신의학",
        "instruments": ["pcl5"],
    },
    "wellbeing_self": {
        "label": "자존감·웰빙",
        "school": "인본주의·긍정심리",
        "instruments": ["rses"],
    },
    "wellbeing_attachment": {
        "label": "애착",
        "school": "관계심리·애착이론",
        "instruments": ["attachment_ecr"],
    },
    "cbt_cognitive": {
        "label": "인지 왜곡",
        "school": "벡 CBT",
        "instruments": ["cbt_thought"],
    },
    "psychodynamic": {
        "label": "방어·반복",
        "school": "프로이트·정신동역학",
        "instruments": ["psychodynamic"],
    },
    "behavioral": {
        "label": "행동·회피",
        "school": "행동주의·BA",
        "instruments": ["behavioral"],
    },
    "projective_htp": {
        "label": "HTP 투사",
        "school": "투사검사",
        "instruments": ["htp"],
    },
    "projective_tarot": {
        "label": "타로 상징",
        "school": "상징·융 투사",
        "instruments": ["tarot_reflect"],
    },
    "humanistic_affect": {
        "label": "감정 온도",
        "school": "로저스·인간중심",
        "instruments": ["micro_emotion"],
    },
    "projective_sct": {
        "label": "문장완성 · 마음 글씨",
        "school": "투사·SCT",
        "instruments": ["sct"],
    },
}

INSTRUMENT_PROFILES: Dict[str, Dict[str, Any]] = {
    "phq9": {
        "display_name": "PHQ-9",
        "domain": "clinical_mood",
        "focus": "우울·무기력·흥미 저하·수면·식욕",
        "keywords": ("우울", "무기력", "의욕", "흥미", "즐거움", "희망", "공허", "식욕", "기운", "피곤", "슬픔", "가라앉"),
        "counseling_fit": ("기분이 가라앉", "아무것도 하기 싫", "우울"),
    },
    "gad7": {
        "display_name": "GAD-7",
        "domain": "clinical_anxiety",
        "focus": "불안·걱정·긴장·초조",
        "keywords": ("불안", "초조", "긴장", "걱정", "두려움", "가슴", "심장", "떨림", "공포"),
        "counseling_fit": ("불안", "걱정이 멈추지", "긴장", "초조"),
    },
    "isi": {
        "display_name": "ISI",
        "domain": "clinical_sleep",
        "focus": "불면·수면 질",
        "keywords": ("잠", "수면", "불면", "깨", "악몽", "피곤", "밤"),
        "counseling_fit": ("잠이 안", "잠들기", "밤마다"),
    },
    "pss": {
        "display_name": "PSS",
        "domain": "clinical_stress",
        "focus": "지각 스트레스",
        "keywords": ("스트레스", "압박", "짜증", "통제", "버거", "지침"),
        "counseling_fit": ("스트레스", "압박", "버거"),
    },
    "pcl5": {
        "display_name": "PCL-5",
        "domain": "clinical_trauma",
        "focus": "외상·플래시백·회피",
        "keywords": ("외상", "트라우마", "악몽", "플래시", "사고", "폭력", "상처"),
        "counseling_fit": ("트라우마", "외상", "악몽"),
    },
    "rses": {
        "display_name": "RSES",
        "domain": "wellbeing_self",
        "focus": "자존감",
        "keywords": ("자존감", "자신", "실패자", "못난", "부족"),
        "counseling_fit": ("자존감", "자신이 없", "실패자"),
    },
    "attachment_ecr": {
        "display_name": "애착 ECR",
        "domain": "wellbeing_attachment",
        "focus": "애착 불안·회피",
        "keywords": ("관계", "버림", "거리", "친밀", "외로", "집착", "회피", "대인"),
        "counseling_fit": ("관계", "사랑", "버릴까", "친해지"),
    },
    "cbt_thought": {
        "display_name": "CBT 사고",
        "domain": "cbt_cognitive",
        "focus": "자동적 사고·인지 왜곡",
        "keywords": ("항상", "절대", "망했", "최악", "실수", "틀렸"),
        "counseling_fit": ("생각", "왜곡", "반복"),
    },
    "psychodynamic": {
        "display_name": "정신동역학",
        "domain": "psychodynamic",
        "focus": "방어·반복 패턴",
        "keywords": ("반복", "방어", "부정", "억누", "무의식", "패턴"),
        "counseling_fit": ("반복", "또 같은", "피하고"),
    },
    "behavioral": {
        "display_name": "행동 활성화",
        "domain": "behavioral",
        "focus": "회피·쾌감 상실",
        "keywords": ("미루", "피하", "나가기 싫", "즐거움 없", "움직이"),
        "counseling_fit": ("미루", "나가기 싫", "아무것도 안"),
    },
    "htp": {
        "display_name": "HTP",
        "domain": "projective_htp",
        "focus": "집·나무·사람 투사",
        "keywords": ("집", "나무", "그림", "상상", "공간"),
        "counseling_fit": ("상상", "비유"),
    },
    "tarot_reflect": {
        "display_name": "타로 투사",
        "domain": "projective_tarot",
        "focus": "상징·아키타입",
        "keywords": ("카드", "타로", "상징", "운명", "전환"),
        "counseling_fit": ("카드", "상징"),
    },
    "micro_emotion": {
        "display_name": "감정 온도",
        "domain": "humanistic_affect",
        "focus": "전반적 감정 강도",
        "keywords": ("힘들", "지침", "모르겠", "복잡", "답답", "막막"),
        "counseling_fit": ("상담", "이야기", "힘들"),
    },
    "sct": {
        "display_name": "문장완성 · SCT",
        "domain": "projective_sct",
        "focus": "자기·관계·미래에 대한 마음 글씨",
        "keywords": ("나는", "자신", "느끼", "힘들", "앞으로", "관계", "엄마", "아버지"),
        "counseling_fit": ("나는", "자신", "느끼는", "써", "말해"),
    },
}


def profile_summary(instrument_id: str) -> str:
    profile = INSTRUMENT_PROFILES.get(instrument_id, {})
    domain = ASSESSMENT_DOMAINS.get(profile.get("domain", ""), {}).get("label", "")
    return f"{profile.get('display_name', instrument_id)} ({domain}): {profile.get('focus', '')}"


def all_instrument_ids() -> List[str]:
    return list(INSTRUMENT_PROFILES.keys())
