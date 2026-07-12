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
    "personality_mbti": {
        "label": "MBTI 선호 탐색",
        "school": "성격심리·유형론(교육용)",
        "instruments": ["mbti_preference"],
    },
    "abnormal_ocd": {
        "label": "강박 탐색",
        "school": "이상심리·Y-BOCS 정보제공",
        "instruments": ["ocd_probe"],
    },
    "abnormal_social": {
        "label": "사회불안 탐색",
        "school": "이상심리·LSAS 정보제공",
        "instruments": ["social_anxiety_probe"],
    },
    "abnormal_panic": {
        "label": "공황 반응 탐색",
        "school": "이상심리·PDSS 정보제공",
        "instruments": ["panic_probe"],
    },
    "abnormal_mania": {
        "label": "기분 고조 탐색",
        "school": "이상심리·MDQ 정보제공",
        "instruments": ["mania_probe"],
    },
    "abnormal_adhd": {
        "label": "주의·실행기능 탐색",
        "school": "이상심리·ASRS 정보제공",
        "instruments": ["adhd_probe"],
    },
    "abnormal_alcohol": {
        "label": "음주 패턴 탐색",
        "school": "이상심리·AUDIT-C 정보제공",
        "instruments": ["alcohol_probe"],
    },
    "abnormal_eating": {
        "label": "식사·몸 이미지 탐색",
        "school": "이상심리·SCOFF 정보제공",
        "instruments": ["eating_probe"],
    },
    "abnormal_dissociation": {
        "label": "해리·거리감 탐색",
        "school": "이상심리",
        "instruments": ["dissociation_probe"],
    },
    "abnormal_somatic": {
        "label": "신체화·몸 신호",
        "school": "이상심리",
        "instruments": ["somatic_probe"],
    },
    "abnormal_anger": {
        "label": "분노·과민 탐색",
        "school": "이상심리",
        "instruments": ["anger_probe"],
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
    "mbti_preference": {
        "display_name": "MBTI 선호",
        "domain": "personality_mbti",
        "focus": "외향·내향·감각·직관·사고·감정·판단·인식 선호",
        "keywords": ("MBTI", "성격", "유형", "외향", "내향", "선호", "에너지"),
        "counseling_fit": ("성격", "MBTI", "유형", "어떤 사람"),
    },
    "ocd_probe": {
        "display_name": "강박 탐색",
        "domain": "abnormal_ocd",
        "focus": "반복 사고·확인 행동",
        "keywords": ("강박", "확인", "반복", "불안해서 또", "씻"),
        "counseling_fit": ("강박", "확인", "반복해서"),
    },
    "social_anxiety_probe": {
        "display_name": "사회불안 탐색",
        "domain": "abnormal_social",
        "focus": "대인 긴장·회피",
        "keywords": ("사람들 앞", "발표", "시선", "부끄", "사회불안", "모임"),
        "counseling_fit": ("사람들", "발표", "눈치", "모임"),
    },
    "panic_probe": {
        "display_name": "공황 탐색",
        "domain": "abnormal_panic",
        "focus": "급격한 불안·신체 반응",
        "keywords": ("공황", "두근거", "숨이", "질식", "패닉"),
        "counseling_fit": ("공황", "숨이", "심장이"),
    },
    "mania_probe": {
        "display_name": "기분 고조 탐색",
        "domain": "abnormal_mania",
        "focus": "에너지·수면·충동 변화",
        "keywords": ("잠 안", "에너지", "들뜬", "충동", "조증"),
        "counseling_fit": ("너무 들떠", "잠이 필요", "충동"),
    },
    "adhd_probe": {
        "display_name": "주의력 탐색",
        "domain": "abnormal_adhd",
        "focus": "집중·실행·안절부절",
        "keywords": ("집중", "산만", "ADHD", "미루", "생각 많"),
        "counseling_fit": ("집중이", "산만", "정리가 안"),
    },
    "alcohol_probe": {
        "display_name": "음주 탐색",
        "domain": "abnormal_alcohol",
        "focus": "스트레스 음주·조절",
        "keywords": ("술", "음주", "취해", "술로"),
        "counseling_fit": ("술", "마시면", "음주"),
    },
    "eating_probe": {
        "display_name": "식사·몸 탐색",
        "domain": "abnormal_eating",
        "focus": "식사 통제·체형 염려",
        "keywords": ("다이어트", "폭식", "체중", "몸무게", "식사"),
        "counseling_fit": ("먹는", "몸무게", "다이어트"),
    },
    "dissociation_probe": {
        "display_name": "해리 탐색",
        "domain": "abnormal_dissociation",
        "focus": "비현실감·공백감",
        "keywords": ("비현실", "안개", "나 같지", "공백", "멍"),
        "counseling_fit": ("현실이", "멍해", "나 같지"),
    },
    "somatic_probe": {
        "display_name": "몸 신호 탐색",
        "domain": "abnormal_somatic",
        "focus": "신체 불편·건강 염려",
        "keywords": ("두통", "가슴", "배가", "몸이", "긴장", "통증"),
        "counseling_fit": ("몸이", "두통", "가슴이"),
    },
    "anger_probe": {
        "display_name": "분노 탐색",
        "domain": "abnormal_anger",
        "focus": "분노·과민·관계 영향",
        "keywords": ("화", "짜증", "분노", "폭발", "참기"),
        "counseling_fit": ("화가", "짜증", "참기 힘들"),
    },
}


def profile_summary(instrument_id: str) -> str:
    profile = INSTRUMENT_PROFILES.get(instrument_id, {})
    domain = ASSESSMENT_DOMAINS.get(profile.get("domain", ""), {}).get("label", "")
    return f"{profile.get('display_name', instrument_id)} ({domain}): {profile.get('focus', '')}"


def all_instrument_ids() -> List[str]:
    return list(INSTRUMENT_PROFILES.keys())
