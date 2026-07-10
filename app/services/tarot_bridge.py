from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.chat_session import ChatSessionState


def build_tarot_handoff(
    user_story: str,
    draw_result: Dict[str, Any],
    reading: Dict[str, Any],
) -> Dict[str, Any]:
    cards = draw_result.get("cards") or []
    card_summaries: List[Dict[str, str]] = []
    for card in cards:
        orientation = "역방향" if card.get("reversed") else "정방향"
        card_summaries.append(
            {
                "position": card.get("position", ""),
                "name_ko": card.get("name_ko", ""),
                "name_en": card.get("name_en", ""),
                "orientation": orientation,
                "meaning": card.get("meaning_ko", ""),
                "psychology_theme": card.get("psychology_theme", ""),
                "archetype": card.get("archetype", ""),
            }
        )

    primary = cards[0] if cards else {}
    bridge_message = build_counselor_bridge_message(user_story, card_summaries, reading)

    return {
        "user_story": user_story.strip(),
        "spread": draw_result.get("spread"),
        "spread_label_ko": draw_result.get("spread_label_ko"),
        "cards": card_summaries,
        "reading_summary": reading.get("summary", ""),
        "ai_analysis": reading.get("ai_analysis", ""),
        "psychology_themes": reading.get("psychology_themes") or [],
        "recommended_actions": reading.get("recommended_actions") or reading.get("cbt_actions") or [],
        "primary_card": primary.get("name_en"),
        "bridge_message": bridge_message,
        "blend_status": "pending",
    }


def build_counselor_bridge_message(
    user_story: str,
    card_summaries: List[Dict[str, str]],
    reading: Dict[str, Any],
) -> str:
    lines: List[str] = []
    if user_story.strip():
        lines.append(f"방금 나눠 주신 '{user_story.strip()[:60]}' 마음, 잘 받았어요.")
    else:
        lines.append("방금 카드로 마음을 함께 들여다봤어요.")

    if card_summaries:
        card_bits = []
        for card in card_summaries:
            card_bits.append(
                f"{card['position']}의 {card['name_ko']}({card['orientation']}) — {card['psychology_theme']}"
            )
        lines.append("카드가 **살짝** 비춘 흐름을 대화에 이어갈게요. " + " / ".join(card_bits) + ".")

    if reading.get("summary"):
        lines.append(reading["summary"])

    lines.append(
        "카드는 **가벼운 거울**이에요. 깊은 해석보다, 지금 와닿는 느낌 하나만 편하게 말씀해 주셔도 충분해요."
    )
    return " ".join(lines)


def apply_tarot_handoff(state: ChatSessionState, handoff: Dict[str, Any]) -> Dict[str, Any]:
    state.tarot_handoff = handoff
    state.tarot_blended = True
    handoff["blend_status"] = "active"
    handoff["session_id"] = state.session_id

    notes = state.phase_notes
    if handoff.get("user_story") and not notes.get("chief_complaint"):
        notes["chief_complaint"] = handoff["user_story"]
    if handoff.get("primary_card"):
        notes["tarot_primary_card"] = handoff["primary_card"]
    if handoff.get("psychology_themes"):
        notes["tarot_themes"] = handoff["psychology_themes"]

    archetypes = [
        card.get("archetype")
        for card in (handoff.get("cards") or [])
        if card.get("archetype")
    ]
    if archetypes:
        notes["tarot_archetypes"] = archetypes

    if state.counseling_phase == "rapport" and state.turn_count >= 2:
        state.counseling_phase = "conceptualization"
        notes["conceptualization_intro_done"] = False

    return {
        "session_id": state.session_id,
        "counseling_phase": state.counseling_phase,
        "bridge_message": handoff.get("bridge_message", ""),
        "tarot_handoff": handoff,
    }


def build_tarot_system_block(state: ChatSessionState) -> str:
    handoff = state.tarot_handoff
    if not handoff or handoff.get("blend_status") != "active":
        return ""

    card_lines = []
    for card in handoff.get("cards") or []:
        card_lines.append(
            f"- {card.get('position')}: {card.get('name_ko')} ({card.get('orientation')}) — "
            f"{card.get('meaning')} [심리 테마: {card.get('psychology_theme')}]"
        )

    actions = handoff.get("recommended_actions") or []
    action_text = "\n".join(f"  · {action}" for action in actions[:3] if action)

    return (
        "\n\n## 타로·상담 블렌드 맥락 (방금 전 타로 리딩과 연결)\n"
        f"내담자 질문/상황: {handoff.get('user_story') or '미입력'}\n"
        f"스프레드: {handoff.get('spread_label_ko') or handoff.get('spread')}\n"
        "뽑힌 카드:\n"
        + "\n".join(card_lines)
        + "\n\n풀이 요약: "
        + (handoff.get("reading_summary") or "")
        + "\n\n상담 지침:\n"
        "- 타로는 **가벼운 거울·은유**로만 언급. 그림자·무의식·원형 **깊은 해석 금지**.\n"
        "- '혹시 ~일 수도 있어요' 톤. 사용자가 원할 때만 조금 더 깊이.\n"
        "- 카드 테마와 실제 이야기를 **부담 없이** 연결하는 질문 1~2개.\n"
        "- 아래 제안은 부담 없이 1개만 자연스럽게:\n"
        + (action_text or "  · (없음)")
    )


def should_suggest_tarot(state: ChatSessionState) -> bool:
    if state.tarot_blended or state.tarot_handoff:
        return False
    if state.counseling_phase not in {"conceptualization", "intervention"}:
        return False
    return state.turn_count >= 3
