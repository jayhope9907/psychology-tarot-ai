"""검사·기법을 사용자 눈높이의 쉬운 말로 풀어 주는 레이어."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# 검사별 — 전문 용어 대신 상담사가 말하듯 소개
INSTRUMENT_USER_VOICE: Dict[str, Dict[str, str]] = {
    "phq9": {
        "user_title": "요즘 마음 기분 들여다보기",
        "intro": "검사라기보다, 요즘 기분·에너지가 어떤지 같이 확인해 보려고요.",
        "example": "예: '요즘 즐거움이 줄었나요?'처럼 편하게 여쭤볼게요.",
    },
    "gad7": {
        "user_title": "걱정·불안한 마음 살펴보기",
        "intro": "불안 척도 이름 대신, 걱정이 얼마나 자주 찾아오는지만 가볍게 볼게요.",
        "example": "맞는 정도만 골라 주시면 돼요. 정답은 없어요.",
    },
    "isi": {
        "user_title": "잠·수면 이야기",
        "intro": "잠들기 어렵거나 자주 깨는지, 수면 쪽 마음을 같이 봐요.",
        "example": "최근 며칠을 떠올리며 답해 주셔도 충분해요.",
    },
    "pss": {
        "user_title": "스트레스·버거움 체크",
        "intro": "요즘 얼마나 압박·짜증·통제 어려움을 느끼는지 여쭤볼게요.",
        "example": "일상에서 느껴지는 정도만 골라 주세요.",
    },
    "pcl5": {
        "user_title": "힘든 기억·마음 반응",
        "intro": "민감할 수 있어요. 편한 만큼만, 힘든 기억이 지금 마음에 어떤 영향을 주는지 봐요.",
        "example": "답하기 어려우면 '지금은 넘어갈게요'를 눌러 주셔도 괜찮아요.",
    },
    "rses": {
        "user_title": "나 자신을 바라보는 마음",
        "intro": "자존감 검사라기보다, 지금 자신을 어떻게 느끼는지 들어보려고요.",
        "example": "예: '지금 혹시 당신이 자신한테 느끼는 것이 무엇인지 써줄 수 있나요?'처럼요.",
    },
    "attachment_ecr": {
        "user_title": "관계·가까움·거리감",
        "intro": "애착 이론 이름 없이, 가까운 사람과의 마음 거리만 살짝 볼게요.",
        "example": "연인·가족·친구 중 떠오르는 관계를 기준으로 해도 돼요.",
    },
    "cbt_thought": {
        "user_title": "자주 드는 생각 패턴",
        "intro": "CBT 전문 용어 대신, '맨날 이런 생각이 든다'는 느낌을 여쭤볼게요.",
        "example": "'최악일 것 같아요', '다 망했어요' 같은 생각이 있는지요.",
    },
    "psychodynamic": {
        "user_title": "반복되는 마음·관계 패턴",
        "intro": "비슷한 상황이 또 오는지, 힘든 감정을 피하게 되는지 가볍게 봐요.",
        "example": "깊은 해석보다 지금 느껴지는 패턴만 말씀해 주셔도 돼요.",
    },
    "behavioral": {
        "user_title": "미루기·피하기·즐거움",
        "intro": "행동 활성화라는 말 대신, 요즘 움직이기·만나기·즐거움이 어떤지만 볼게요.",
        "example": "해야 할 일을 미루거나, 예전 즐거움이 줄었는지요.",
    },
    "htp": {
        "user_title": "집·나무·사람으로 상상하기",
        "intro": "그림을 그리는 HTP 대신, 상상으로 마음을 비유해 볼 거예요.",
        "example": "예: '지금 마음이 집이라면 어떤 느낌일까요?'",
    },
    "tarot_reflect": {
        "user_title": "지금 마음에 닿는 상징 고르기",
        "intro": "타로는 점이 아니라, 지금 마음과 닿는 이미지를 고르는 시간이에요.",
        "example": "끌리는 느낌 하나만 골라 주세요.",
    },
    "micro_emotion": {
        "user_title": "지금 이 순간 마음 무게",
        "intro": "숫자 검사가 아니라, 지금 마음이 얼마나 무겁거나 가벼운지만 볼게요.",
        "example": "딱 맞지 않아도 가장 가까운 쪽을 골라 주세요.",
    },
    "sct": {
        "user_title": "문장 이어쓰기 · 마음 글씨",
        "intro": "SCT(문장완성검사)처럼, 시작 문장 뒤에 지금 마음을 자유롭게 이어 써 주세요.",
        "example": "예: '나에게 나란…' / '힘들 때 나는…' — 한두 문장이면 충분해요.",
    },
    "mbti_preference": {
        "user_title": "나의 에너지·결정 스타일 (MBTI)",
        "intro": "유형을 정하려는 게 아니에요. 에너지·정보·결정·생활 취향만 가볍게 살펴요.",
        "example": "왼쪽·오른쪽 중 요즘 마음에 가까운 쪽만 골라 주세요.",
    },
    "ocd_probe": {
        "user_title": "반복되는 생각·확인",
        "intro": "강박이라는 말 대신, 생각이 맴돌거나 확인을 반복하는지 살짝 볼게요.",
        "example": "부담되면 건너뛰셔도 괜찮아요.",
    },
    "social_anxiety_probe": {
        "user_title": "사람들 앞에서의 긴장",
        "intro": "대인관계에서 긴장·부끄러움이 얼마나 자주 오는지 편하게 여쭤볼게요.",
        "example": "모임·발표·시선이 떠오르면 그 기준으로요.",
    },
    "panic_probe": {
        "user_title": "갑자기 밀려오는 불안",
        "intro": "몸이 먼저 놀란 경험이 있는지, 부드럽게만 확인할게요.",
        "example": "없으면 ‘거의 없어요’를 골라 주세요.",
    },
    "mania_probe": {
        "user_title": "기분이 높이 올라간 시기",
        "intro": "가라앉음뿐 아니라, 에너지가 과하게 오른 시기도 함께 보면 입체적이에요.",
        "example": "잘잘못을 따지지 않아요.",
    },
    "adhd_probe": {
        "user_title": "집중·정리의 어려움",
        "intro": "ADHD 진단이 아니라, 집중·실행이 얼마나 버거운지만 볼게요.",
        "example": "일·공부·대화 중 떠오르는 장면으로요.",
    },
    "alcohol_probe": {
        "user_title": "술과 스트레스",
        "intro": "비난 없이, 술을 찾는 패턴만 가볍게 살펴요.",
        "example": "답하기 어려우면 넘어가셔도 됩니다.",
    },
    "eating_probe": {
        "user_title": "식사·몸에 대한 마음",
        "intro": "민감할 수 있어요. 편한 만큼만, 식사·체형 걱정을 볼게요.",
        "example": "부담되면 건너뛰어도 전혀 괜찮아요.",
    },
    "dissociation_probe": {
        "user_title": "현실과의 거리감",
        "intro": "안개·공백·나 같지 않음 같은 느낌이 있었는지 살짝 여쭤볼게요.",
        "example": "무서운 질문이 아니에요.",
    },
    "somatic_probe": {
        "user_title": "몸이 말하는 신호",
        "intro": "마음이 힘들 때 몸이 먼저 아플 수 있어요. 몸 신호만 가볍게요.",
        "example": "두통·가슴·배·근육 긴장 등요.",
    },
    "anger_probe": {
        "user_title": "화·짜증이 올라올 때",
        "intro": "감정 에너지가 화 쪽으로 쓰이는지, 관계에 영향이 있는지 볼게요.",
        "example": "비난이 아닌 이해용이에요.",
    },
}

# 문항별 — SCT·자존감 등 쉬운 질문으로 재구성
ITEM_USER_VOICE: Dict[str, Dict[str, str]] = {
    "rses_q1": {
        "prompt": "지금 혹시 당신이 자신한테 느끼는 것이 무엇인지, 한 문장으로 써줄 수 있나요?",
        "framing": "예: '나는…'으로 시작해 보셔도 되고, 아래에서 가장 가까운 느낌을 골라 주셔도 돼요.",
        "example": "예) '나는 요즘 자신이 없어요' · '나는 그럭저럭 괜찮은 사람 같아요'",
    },
    "rses_q2": {
        "prompt": "요즘 나 자신의 좋은 점·버티는 힘, 하나만 떠올린다면 무엇인가요?",
        "framing": "잘 안 떠오르면 '지금은 잘 모르겠어요'라고 써 주셔도 괜찮아요.",
    },
    "ecr_anxiety": {
        "prompt": "가까운 사람이 나를 떠날까 봐 자주 불안하거나 걱정되나요?",
        "framing": "연인·가족·친구 중 편한 관계를 떠올리며 답해 주세요.",
    },
    "ecr_avoidance": {
        "prompt": "너무 가까워지면 부담스러워서 거리를 두고 싶어질 때가 있나요?",
        "framing": "친밀함과 혼자만의 공간, 둘 다 소중해요.",
    },
    "cbt_all_or_nothing": {
        "prompt": "실수하거나 일이 틀어지면 '이제 다 망했어'처럼 느껴질 때가 있나요?",
        "framing": "생각이 그렇게 튀어나오는 빈도만 보면 돼요.",
    },
    "cbt_catastrophize": {
        "prompt": "앞일이 최악으로 흘러갈 것 같다는 상상이 자주 드나요?",
        "framing": "걱정의 '크기'보다 자주 드는지만 골라 주세요.",
    },
    "pd_repetition": {
        "prompt": "비슷한 관계·상황이 또 반복되는 느낌이 있나요?",
        "framing": "패턴이라고 부르기 부담스러우면 '익숙한 일' 정도로 생각해 주세요.",
    },
    "pd_defense": {
        "prompt": "힘든 감정이 올라올 때, 모르는 척하거나 바로 다른 일로 바꾸게 되나요?",
        "framing": "피하는 게 나쁜 게 아니에요. 얼마나 자주 그러는지만 볼게요.",
    },
    "ba_avoidance": {
        "prompt": "해야 할 일·약속·만남을 미루거나 피한 적이 요즘 많나요?",
        "framing": "쉬고 싶어서인지, 버거워서인지 구분하지 않아도 돼요.",
    },
    "ba_pleasure": {
        "prompt": "예전에 즐기던 일에서 기쁨·재미가 줄었나요?",
        "framing": "취미·산책·대화·음식 등 뭐든 괜찮아요.",
    },
    "htp_house": {
        "prompt": "지금 마음을 '집'에 비유한다면, 어떤 느낌에 가깝나요?",
        "framing": "크기·문·창문·안전함 등 떠오르는 느낌 하나만 골라 주세요.",
    },
    "htp_tree": {
        "prompt": "당신의 '나무(힘·성장)'는 지금 어떤 상태에 가깝나요?",
        "framing": "튼튼함·마름·흔들림 등 상상으로 고르면 돼요.",
    },
    "htp_person": {
        "prompt": "마음속 '사람(나·타인)'의 모습은 지금 어떤가요?",
        "framing": "크기·방향·긴장감 중 가장 와닿는 쪽을 골라 주세요.",
    },
    "tarot_card": {
        "prompt": "지금 마음에 가장 가까운 그림·느낌을 골라 주세요.",
        "framing": "타로 이름보다 느낌이 중요해요. 끌리는 하나면 충분합니다.",
    },
    "sct_self": {
        "prompt": "지금 혹시 당신이 자신한테 느끼는 것이 무엇인지, 이어서 써 주실 수 있나요?",
        "framing": "문장은 '나에게 나란 …'처럼 이어 써도 되고, 한두 문장이면 충분해요.",
        "example": "예) 나에게 나란 아직 찾는 중이에요 / 나에게 나란 버티는 사람이에요",
        "placeholder": "이어서 자유롭게 써 주세요…",
    },
    "sct_mother": {
        "prompt": "어머니(또는 나를 키운 분)는 …",
        "framing": "가족 이야기가 부담스러우면 '지금은 넘어갈게요'를 눌러 주세요.",
        "placeholder": "떠오르는 대로 한두 문장…",
    },
    "sct_stress": {
        "prompt": "힘들 때 나는 …",
        "framing": "스트레스·슬픔·화가 날 때 자연스럽게 하는 행동이나 마음을 적어 주세요.",
        "placeholder": "예) 혼자 있고 싶어요 / 누군가에게 말하고 싶어요",
    },
    "sct_future": {
        "prompt": "앞으로 나는 …",
        "framing": "희망·걱정·막막함 등 미래에 대한 마음을 이어 써 주세요.",
        "placeholder": "예) 조금씩 나아지고 싶어요",
    },
    "pcl5_q1": {
        "prompt": "힘든 기억이 떠오르거나, 꿈·악몽으로 자주 되살아나나요?",
        "framing": "너무 자세히 쓰지 않으셔도 돼요. 빈도만 골라 주세요.",
    },
    "pcl5_q2": {
        "prompt": "그 일을 떠올리게 하는 것을 피하려 한 적이 있나요?",
        "framing": "회피는 자연스러운 반응이에요. 편한 만큼만 답해 주세요.",
    },
}

FRIENDLY_OPTION_LABELS: Dict[str, str] = {
    "전혀 없음": "전혀 없었어요",
    "며칠": "며칠 정도 그랬어요",
    "절반 이상": "절반 넘는 날 그랬어요",
    "거의 매일": "거의 매일 그랬어요",
    "전혀 아님": "전혀 그렇지 않아요",
    "아닌 편": "그렇지 않은 편이에요",
    "보통": "보통이에요",
    "그런 편": "그런 편이에요",
    "매우 그럼": "꽤 그런 편이에요",
    "아니요": "아니요, 잘 모르겠어요",
    "가끔": "가끔 그래요",
    "자주": "자주 그래요",
    "거의 항상": "거의 항상 그래요",
    "거의 없음": "거의 없었어요",
    "때때로": "때때로 그랬어요",
    "자주": "자주 그랬어요",
    "매우 자주": "매우 자주 그랬어요",
}


def user_instrument_title(instrument_id: str) -> str:
    voice = INSTRUMENT_USER_VOICE.get(instrument_id, {})
    return voice.get("user_title") or voice.get("title") or ""


def user_instrument_delivery() -> str:
    return "대화처럼 한 가지만 · 편하면 넘어가도 OK"


def friendly_options(options: List[Dict[str, Any]], response_type: str = "") -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for opt in options:
        label = str(opt.get("label") or "")
        friendly = FRIENDLY_OPTION_LABELS.get(label, label)
        out.append({**opt, "label": friendly})
    return out


def enrich_assessment_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """오케스트레이터·API가 내려주는 검사 카드에 쉬운 말을 입힌다."""
    instrument = str(payload.get("instrument") or "")
    item_id = str(payload.get("item_id") or "")
    voice = INSTRUMENT_USER_VOICE.get(instrument, {})
    item_voice = ITEM_USER_VOICE.get(item_id, {})

    payload["user_title"] = user_instrument_title(instrument) or "마음 들여다보기"
    payload["user_intro"] = voice.get("intro", "")
    payload["example"] = item_voice.get("example") or voice.get("example", "")
    if item_voice.get("placeholder"):
        payload["placeholder"] = item_voice["placeholder"]

    if item_voice.get("prompt"):
        payload["prompt"] = item_voice["prompt"]
    if item_voice.get("framing"):
        payload["framing"] = item_voice["framing"]
    elif voice.get("intro"):
        base = (payload.get("framing") or "").strip()
        payload["framing"] = f"{voice['intro']}\n\n{base}".strip() if base else voice["intro"]

    payload["counselor_note"] = (
        payload.get("counselor_note") or "편한 만큼만 나눠 주세요. 지금은 넘어가도 괜찮아요."
    )
    payload["options"] = friendly_options(payload.get("options") or [], payload.get("response_type", ""))
    return payload


def enrich_instrument_step(step: Dict[str, Any]) -> Dict[str, Any]:
    iid = step.get("instrument_id", "")
    title = user_instrument_title(iid)
    if title:
        step = {**step, "title": title, "user_title": title}
    step["delivery"] = user_instrument_delivery()
    return step
