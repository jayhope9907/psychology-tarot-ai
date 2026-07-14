"""오프라인 AI 상담 fallback (검사·스트리밍 API 없이 기본 공감 대화)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

DEFAULT_OFFLINE_REPLY = (
    "말씀해 주셔서 고마워요. 지금은 연결이 약해서 짧게만 답할 수 있어요. "
    "천천히 괜찮아질 거예요. 급하면 📞 1393·119·129도 도움이 됩니다."
)

OFFLINE_ASSESSMENT_NOTICE = (
    "지금은 오프라인이라 **마음 검사**는 할 수 없어요. "
    "인터넷이 연결되면 이어서 검사와 맞춤 상담을 받을 수 있습니다."
)

COUNSEL_OFFLINE_RULES: List[Dict[str, Any]] = [
    {
        "id": "crisis",
        "keywords": ("죽고", "자살", "끝내", "사라지", "목숨", "죽을"),
        "reply": (
            "지금 많이 힘든 것 같아요. 혼자 버티지 않으셔도 돼요. "
            "📞 1393(24시간)·119·129·1577-0199로 바로 연결할 수 있어요. "
            "곁에 있는 사람에게 도움을 요청하셔도 괜찮아요."
        ),
        "crisis": True,
    },
    {
        "id": "distress",
        "keywords": ("힘들", "버틸", "견딜", "무너", "한계", "지쳤"),
        "reply": (
            "많이 지치셨군요. 지금까지 버텨 오신 것만으로도 대단해요. "
            "오늘은 아주 작은 것 하나만 — 물 한 잔, 창문 열기처럼 — 해도 충분해요."
        ),
        "alternates": [
            "많이 지치셨군요. 지금은 작은 것 하나만 해도 충분해요.",
            "버티고 계신 마음, 잘 느껴져요. 오늘 하루 중 가장 버거운 순간이 언제였나요?",
            "지친 마음이 전해져요. 지금 몸은 어떤 상태인지도 함께 살펴봐도 좋아요.",
        ],
    },
    {
        "id": "sad",
        "keywords": ("슬프", "우울", "눈물", "울", "공허", "무기력"),
        "reply": (
            "슬픈 마음이 크게 느껴져요. 그 감정은 자연스러운 거예요. "
            "지금 느끼는 것을 한 단어·그림으로만 적어 봐도 좋아요."
        ),
    },
    {
        "id": "anxious",
        "keywords": ("불안", "걱정", "무서", "두렵", "긴장", "떨"),
        "reply": (
            "불안이 올라온 것 같아요. 숨을 천천히 — 들이마시고, 잠깐 멈추고, 내쉬어 볼까요? "
            "지금 이 순간, 당장 안전한 곳에 있다는 것만 느껴도 괜찮아요."
        ),
        "alternates": [
            "불안이 올라온 것 같아요. 지금 이 순간 몸을 의자에 기대어 보는 것만으로도 괜찮아요.",
            "걱정이 크게 느껴지는군요. 어떤 상황에서 특히 불안이 커지나요?",
            "무서운 마음이 있다면 그 감정부터 인정해 봐도 좋아요. 지금 가장 불안한 포인트는 무엇인가요?",
        ],
    },
    {
        "id": "angry",
        "keywords": ("화", "짜증", "분노", "억울", "미워"),
        "reply": (
            "화가 나는 마음도 충분히 이해해요. "
            "지금 가장 불편한 점이 무엇인지, 편한 만큼만 더 들려주실 수 있을까요?"
        ),
    },
    {
        "id": "lonely",
        "keywords": ("외롭", "혼자", "고립", "쓸쓸", "외로"),
        "reply": (
            "외로움이 크게 느껴지는군요. 혼자가 아니에요 — 지금 이 대화도 연결의 한 조각이에요. "
            "믿을 수 있는 사람에게 짧은 메시지 하나를 보내봐도 좋아요."
        ),
    },
    {
        "id": "sleep",
        "keywords": ("잠", "불면", "악몽", "피곤", "수면"),
        "reply": (
            "잠이 어려우시군요. 오늘 밤은 완벽한 수면을 목표로 하지 않아도 괜찮아요. "
            "눈을 감고 몸만 편하게 두는 것부터 시작해 봐요."
        ),
    },
    {
        "id": "work",
        "keywords": ("직장", "회사", "상사", "업무", "일", "스트레스"),
        "reply": (
            "일과 관련된 부담이 크군요. 통제할 수 있는 작은 한 가지와 "
            "통제하기 어려운 것을 나눠 보면 마음이 조금 가벼워질 수 있어요."
        ),
        "alternates": [
            "직장 이야기군요. 요즘 특히 버거운 순간은 언제인가요?",
            "업무 스트레스가 크게 느껴져요. 상사·동료·업무 중 어디가 가장 힘든가요?",
            "회사에서 마음이 무거울 때, 몸은 어떻게 반응하나요?",
        ],
    },
    {
        "id": "relationship",
        "keywords": ("연애", "이별", "가족", "부모", "친구", "관계", "싸웠"),
        "reply": (
            "관계에서 마음이 많이 움직이는 것 같아요. "
            "상대의 말보다, 지금 내 마음이 어떤지부터 천천히 살펴봐도 좋아요."
        ),
    },
    {
        "id": "thanks",
        "keywords": ("고마", "감사", "도움"),
        "reply": "천만에요. 편한 속도로 계속 이야기해 주셔도 괜찮아요.",
    },
    {
        "id": "greeting",
        "keywords": ("안녕", "처음", "시작"),
        "reply": (
            "안녕하세요. 지금은 오프라인 모드라 짧게 답하고 있어요. "
            "편한 만큼만 마음을 나눠 주세요. 연결되면 더 깊은 상담을 이어갈 수 있어요."
        ),
    },
]


def counsel_offline_bundle() -> Dict[str, Any]:
    return {
        "bundle_version": 1,
        "mode": "offline_counseling",
        "default_reply": DEFAULT_OFFLINE_REPLY,
        "assessment_blocked_notice": OFFLINE_ASSESSMENT_NOTICE,
        "rules": COUNSEL_OFFLINE_RULES,
        "crisis_resources": [
            {"label": "1393 자살예방", "tel": "1393"},
            {"label": "119 응급", "tel": "119"},
            {"label": "129 보건복지", "tel": "129"},
            {"label": "1577-0199", "tel": "1577-0199"},
        ],
    }


def match_offline_counsel_reply(message: str, turn_index: int = 0) -> Dict[str, Any]:
    blob = (message or "").strip().lower()
    if not blob:
        return {"reply_text": DEFAULT_OFFLINE_REPLY, "rule_id": "empty", "offline": True}
    for rule in COUNSEL_OFFLINE_RULES:
        if any(kw in blob for kw in rule["keywords"]):
            replies = list(rule.get("alternates") or []) or [rule["reply"]]
            reply_text = replies[turn_index % len(replies)]
            return {
                "reply_text": reply_text,
                "rule_id": rule["id"],
                "crisis": bool(rule.get("crisis")),
                "offline": True,
            }
    return {"reply_text": DEFAULT_OFFLINE_REPLY, "rule_id": "default", "offline": True}
