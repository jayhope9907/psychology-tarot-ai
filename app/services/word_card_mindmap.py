"""Warm word-card game + conscious/unconscious boundary + mindmap model.

Non-diagnostic wellness module:
  1) Word card deck (감정/몸/관계/바람) — tap-to-pick instead of typing.
  2) Allowlist parser: raw selections are sanitized against the deck before
     they ever reach the AI stream (mirrors input_sanitizer contract).
  3) Boundary analysis: each card carries a conscious-awareness bias, so the
     agent can gently ask whether a feeling is a known mind (의식) or a
     deeper one that slipped out (무의식) — always in a warm, human tone.
  4) Mindmap model: "지금의 나" centered radial map built from picked cards,
     conversation keywords, and the user's stress-management tracking.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

DECK_VERSION = "1.0"
MAX_SELECTED_CARDS = 8

# awareness_bias: 0.0 = 깊은 곳(무의식 쪽), 1.0 = 스스로 잘 아는 마음(의식 쪽)
WORD_CARD_DECK: List[Dict[str, Any]] = [
    # 감정 (feelings)
    {"id": "joy", "label_ko": "기쁨", "category": "감정", "awareness_bias": 0.85, "valence": 1},
    {"id": "calm", "label_ko": "차분함", "category": "감정", "awareness_bias": 0.8, "valence": 1},
    {"id": "anxious", "label_ko": "불안", "category": "감정", "awareness_bias": 0.6, "valence": -1},
    {"id": "sadness", "label_ko": "슬픔", "category": "감정", "awareness_bias": 0.55, "valence": -1},
    {"id": "anger", "label_ko": "화남", "category": "감정", "awareness_bias": 0.65, "valence": -1},
    {"id": "emptiness", "label_ko": "공허함", "category": "감정", "awareness_bias": 0.25, "valence": -1},
    {"id": "longing", "label_ko": "그리움", "category": "감정", "awareness_bias": 0.3, "valence": 0},
    {"id": "guilt", "label_ko": "미안함", "category": "감정", "awareness_bias": 0.35, "valence": -1},
    # 몸·상태 (body / state)
    {"id": "tired", "label_ko": "지침", "category": "몸", "awareness_bias": 0.8, "valence": -1},
    {"id": "tense", "label_ko": "긴장됨", "category": "몸", "awareness_bias": 0.6, "valence": -1},
    {"id": "heavy_chest", "label_ko": "가슴 답답", "category": "몸", "awareness_bias": 0.45, "valence": -1},
    {"id": "sleepless", "label_ko": "잠 설침", "category": "몸", "awareness_bias": 0.7, "valence": -1},
    {"id": "numb", "label_ko": "무감각", "category": "몸", "awareness_bias": 0.2, "valence": -1},
    {"id": "light_body", "label_ko": "몸 가벼움", "category": "몸", "awareness_bias": 0.8, "valence": 1},
    # 관계 (relations)
    {"id": "lonely", "label_ko": "외로움", "category": "관계", "awareness_bias": 0.4, "valence": -1},
    {"id": "pressure", "label_ko": "눈치 보임", "category": "관계", "awareness_bias": 0.45, "valence": -1},
    {"id": "grateful", "label_ko": "고마움", "category": "관계", "awareness_bias": 0.75, "valence": 1},
    {"id": "distant", "label_ko": "멀어진 느낌", "category": "관계", "awareness_bias": 0.3, "valence": -1},
    {"id": "mask", "label_ko": "괜찮은 척", "category": "관계", "awareness_bias": 0.2, "valence": -1},
    {"id": "wanted_talk", "label_ko": "말하고 싶음", "category": "관계", "awareness_bias": 0.55, "valence": 0},
    # 바람 (wishes)
    {"id": "rest", "label_ko": "쉬고 싶음", "category": "바람", "awareness_bias": 0.75, "valence": 0},
    {"id": "escape", "label_ko": "떠나고 싶음", "category": "바람", "awareness_bias": 0.35, "valence": 0},
    {"id": "recognition", "label_ko": "인정받고 싶음", "category": "바람", "awareness_bias": 0.3, "valence": 0},
    {"id": "hug", "label_ko": "위로받고 싶음", "category": "바람", "awareness_bias": 0.4, "valence": 0},
]

_DECK_BY_ID: Dict[str, Dict[str, Any]] = {card["id"]: card for card in WORD_CARD_DECK}
_DECK_BY_LABEL: Dict[str, Dict[str, Any]] = {card["label_ko"]: card for card in WORD_CARD_DECK}

CONSCIOUS_THRESHOLD = 0.6
UNCONSCIOUS_THRESHOLD = 0.4

# Conversation keyword lexicon for mindmap branches (allowlist, non-PII).
CONVERSATION_KEYWORDS = (
    "가족", "회사", "학교", "친구", "연애", "관계", "잠", "꿈",
    "돈", "건강", "미래", "과거", "일", "공부", "혼자", "집",
)


def get_word_card_deck() -> Dict[str, Any]:
    """Deck payload for the WordCardGame UI."""
    categories: Dict[str, List[Dict[str, Any]]] = {}
    for card in WORD_CARD_DECK:
        categories.setdefault(card["category"], []).append(
            {"id": card["id"], "label_ko": card["label_ko"], "category": card["category"]}
        )
    return {
        "deckVersion": DECK_VERSION,
        "maxSelect": MAX_SELECTED_CARDS,
        "categories": [
            {"category": cat, "cards": cards} for cat, cards in categories.items()
        ],
        "guide_ko": "마음에 와닿는 낱말을 편하게 골라 주세요. 정답은 없어요.",
        "non_diagnostic": True,
    }


def sanitize_word_card_selection(raw: Any) -> List[Dict[str, Any]]:
    """Allowlist parser: only known deck cards survive; free text is dropped.

    Accepts a list of card ids or Korean labels; caps at MAX_SELECTED_CARDS;
    dedupes while preserving order.
    """
    if not isinstance(raw, (list, tuple)):
        return []
    out: List[Dict[str, Any]] = []
    seen: set = set()
    for item in raw:
        key = str(item or "").strip()
        card = _DECK_BY_ID.get(key) or _DECK_BY_LABEL.get(key)
        if not card or card["id"] in seen:
            continue
        seen.add(card["id"])
        out.append(dict(card))
        if len(out) >= MAX_SELECTED_CARDS:
            break
    return out


def _layer_of(bias: float) -> str:
    if bias >= CONSCIOUS_THRESHOLD:
        return "conscious"
    if bias <= UNCONSCIOUS_THRESHOLD:
        return "unconscious"
    return "boundary"


def analyze_conscious_boundary(
    selection: Iterable[Mapping[str, Any]],
    *,
    psychodynamic_metrics: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Classify picked cards into conscious / boundary / unconscious layers."""
    cards = [dict(c) for c in selection]
    layers: Dict[str, List[Dict[str, Any]]] = {"conscious": [], "boundary": [], "unconscious": []}
    for card in cards:
        bias = float(card.get("awareness_bias", 0.5))
        layer = _layer_of(bias)
        layers[layer].append(
            {"id": card["id"], "label_ko": card["label_ko"], "awarenessBias": bias, "layer": layer}
        )

    biases = [float(c.get("awareness_bias", 0.5)) for c in cards]
    boundary_score = round(sum(biases) / len(biases), 3) if biases else 0.5

    metrics = dict(psychodynamic_metrics or {})
    archetype = metrics.get("dominant_archetype") or metrics.get("dominantArchetype")

    deep = layers["unconscious"] + layers["boundary"]
    focus_deep = deep[0]["label_ko"] if deep else None
    focus_known = layers["conscious"][0]["label_ko"] if layers["conscious"] else None

    return {
        "deckVersion": DECK_VERSION,
        "selectedCount": len(cards),
        "selected": [
            {"id": c["id"], "label_ko": c["label_ko"], "category": c["category"]} for c in cards
        ],
        "layers": layers,
        "boundaryScore": boundary_score,
        "boundaryReadingKo": (
            "스스로 잘 아는 마음 쪽에 가까워요"
            if boundary_score >= CONSCIOUS_THRESHOLD
            else "깊은 곳 마음이 함께 올라오고 있어요"
            if boundary_score <= UNCONSCIOUS_THRESHOLD
            else "의식과 무의식의 경계선 위에 있어요"
        ),
        "focusDeepKo": focus_deep,
        "focusKnownKo": focus_known,
        "dominantArchetype": archetype,
        "non_diagnostic": True,
    }


def build_warm_boundary_question(
    analysis: Mapping[str, Any],
    *,
    display_name: str = "",
) -> str:
    """Human, warm boundary question (never a cold test tone)."""
    name = (display_name or "").strip()
    prefix = f"{name}님, " if name else ""
    deep = analysis.get("focusDeepKo")
    known = analysis.get("focusKnownKo")

    if deep and known:
        return (
            f"{prefix}‘{known}’은 스스로도 잘 알고 계신 마음(의식) 같고, "
            f"‘{deep}’은 나도 모르게 툭 튀어나온 깊은 곳의 마음(무의식)일 수도 있겠어요. "
            "둘 중 어느 쪽이 지금 더 크게 느껴지는지, 함께 천천히 알아가 봐요."
        )
    if deep:
        return (
            f"{prefix}고르신 ‘{deep}’은 평소에 잘 드러나지 않던, "
            "깊은 곳에서 조용히 올라온 마음일 수도 있어요. "
            "이 낱말이 왜 마음에 와닿았는지, 함께 천천히 알아가 봐요."
        )
    if known:
        return (
            f"{prefix}‘{known}’이라고 골라 주신 마음, 스스로 잘 들여다보고 계신 것 같아요. "
            "그 마음 아래에 또 다른 결이 있는지도 같이 살펴볼까요?"
        )
    return (
        f"{prefix}지금 하신 말씀은 스스로도 잘 알고 계신 마음(의식)일까요? "
        "아니면 나도 모르게 툭 튀어나온 깊은 곳의 마음(무의식)일까요? "
        "함께 천천히 알아가 봐요."
    )


def build_word_card_prompt_block(
    analysis: Mapping[str, Any],
    *,
    display_name: str = "",
) -> str:
    """System-prompt binding so the AI keeps the warm boundary framing."""
    if not analysis or not analysis.get("selectedCount"):
        return ""
    labels = ", ".join(c["label_ko"] for c in (analysis.get("selected") or []))
    layers = analysis.get("layers") or {}
    deep_labels = ", ".join(
        n["label_ko"] for n in (layers.get("unconscious") or []) + (layers.get("boundary") or [])
    )
    lines = [
        "## 낱말카드 놀이 — 의식/무의식 경계 반영 (비진단, 따뜻한 어조 필수)",
        f"- 내담자가 고른 낱말카드: {labels}",
        f"- 경계 지표 boundaryScore={analysis.get('boundaryScore')} → {analysis.get('boundaryReadingKo')}",
    ]
    if deep_labels:
        lines.append(f"- 깊은 곳(무의식 쪽) 신호 낱말: {deep_labels}")
    lines.extend(
        [
            "- 검사·분석 같은 딱딱한 표현 금지. '마음', '낱말', '함께 알아가요' 같은 부드러운 표현만 사용.",
            "- 아래 예시 톤으로, 고른 낱말이 '스스로 아는 마음(의식)'인지 '툭 튀어나온 깊은 마음(무의식)'인지 부드럽게 한 번만 물어보세요.",
            f"  예시: \"{build_warm_boundary_question(analysis, display_name=display_name)}\"",
            "- 진단 단정 금지. 낱말은 내담자가 스스로 자신을 돌아보는 거울로만 사용하세요.",
        ]
    )
    return "\n".join(lines)


def extract_conversation_keywords(messages: Iterable[Mapping[str, Any]], limit: int = 6) -> List[str]:
    """Allowlist keyword scan over recent user messages (no free-text leakage)."""
    found: List[str] = []
    for entry in list(messages)[-12:]:
        if entry.get("role") != "user":
            continue
        text = str(entry.get("content") or "")
        for kw in CONVERSATION_KEYWORDS:
            if kw in text and kw not in found:
                found.append(kw)
    return found[:limit]


def build_mindmap_model(
    *,
    user_id: str,
    analysis: Mapping[str, Any],
    conversation_keywords: Optional[List[str]] = None,
    stress_summary: Optional[Mapping[str, Any]] = None,
    display_name: str = "",
) -> Dict[str, Any]:
    """'지금 현재의 나' 시각화 마인드맵 데이터 모델.

    Center node + 4 branches: 의식 / 경계·무의식 / 대화 키워드 / 스트레스 돌봄.
    Frontend MindmapView renders this radially; stress branch links to the
    stress-management tracking so the user can revisit their own care record.
    """
    layers = (analysis or {}).get("layers") or {}
    keywords = conversation_keywords or []
    stress = dict(stress_summary or {})

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    center = {"id": "me_now", "label_ko": "지금의 나", "kind": "center", "weight": 1.0}
    nodes.append(center)

    def _branch(branch_id: str, label: str, children: List[Dict[str, Any]], color: str) -> None:
        if not children:
            return
        bnode = {"id": branch_id, "label_ko": label, "kind": "branch", "color": color, "weight": 0.8}
        nodes.append(bnode)
        edges.append({"from": "me_now", "to": branch_id})
        for child in children:
            nodes.append(child)
            edges.append({"from": branch_id, "to": child["id"]})

    _branch(
        "conscious",
        "알고 있는 마음 (의식)",
        [
            {"id": f"c_{n['id']}", "label_ko": n["label_ko"], "kind": "word", "layer": "conscious", "weight": 0.6}
            for n in (layers.get("conscious") or [])
        ],
        "#7cb8f2",
    )
    _branch(
        "deep",
        "깊은 곳 마음 (경계·무의식)",
        [
            {"id": f"d_{n['id']}", "label_ko": n["label_ko"], "kind": "word", "layer": n["layer"], "weight": 0.6}
            for n in (layers.get("boundary") or []) + (layers.get("unconscious") or [])
        ],
        "#b393e8",
    )
    _branch(
        "talk",
        "요즘 이야기 키워드",
        [
            {"id": f"k_{i}", "label_ko": kw, "kind": "keyword", "weight": 0.5}
            for i, kw in enumerate(keywords)
        ],
        "#f2b96b",
    )

    stress_children: List[Dict[str, Any]] = []
    tick_count = int(stress.get("tickCount") or 0)
    if tick_count:
        stress_children.append(
            {
                "id": "s_resets",
                "label_ko": f"3분 리셋 {tick_count}회",
                "kind": "stress",
                "weight": 0.6,
                "link": "stress_management_history",
            }
        )
    latest = stress.get("latest") or {}
    if latest.get("preSud") is not None:
        stress_children.append(
            {
                "id": "s_sud",
                "label_ko": f"최근 힘듦 {latest.get('preSud')}/10",
                "kind": "stress",
                "weight": 0.5,
            }
        )
    _branch("care", "스트레스 돌봄 기록", stress_children, "#8fd6a8")

    return {
        "version": "1.0",
        "userId": user_id,
        "titleKo": (f"{display_name}님의 " if display_name else "") + "지금 마음 지도",
        "centerNodeId": "me_now",
        "nodes": nodes,
        "edges": edges,
        "boundaryScore": (analysis or {}).get("boundaryScore"),
        "boundaryReadingKo": (analysis or {}).get("boundaryReadingKo"),
        "reflectionPromptKo": (
            "지도를 천천히 바라보며, 지금의 나에게 가장 가까운 낱말 하나를 골라 보세요. "
            "그 낱말이 오늘 나에게 해 주고 싶은 말은 무엇일까요?"
        ),
        "non_diagnostic": True,
    }
