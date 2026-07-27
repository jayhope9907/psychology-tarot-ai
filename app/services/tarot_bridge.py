from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.chat_session import ChatSessionState
from app.services.clinical_pipeline import extract_tarot_signals


def _clip(text: str, limit: int) -> str:
    t = (text or "").strip()
    if len(t) <= limit:
        return t
    cut = t[: limit - 1].rsplit(" ", 1)[0]
    return (cut or t[: limit - 1]).rstrip() + "…"


def build_tarot_handoff(
    user_story: str,
    draw_result: Dict[str, Any],
    reading: Dict[str, Any],
) -> Dict[str, Any]:
    cards = draw_result.get("cards") or []
    card_summaries: List[Dict[str, str]] = []
    for card in cards:
        orientation = "역방향" if card.get("reversed") else card.get("orientation") or "정방향"
        if orientation not in ("정방향", "역방향"):
            orientation = "역방향" if card.get("reversed") else "정방향"
        card_summaries.append(
            {
                "position": card.get("position", ""),
                "name_ko": card.get("name_ko", ""),
                "name_en": card.get("name_en", ""),
                "orientation": orientation,
                "meaning": card.get("meaning_ko") or card.get("meaning") or "",
                "psychology_theme": card.get("psychology_theme", ""),
                "archetype": card.get("archetype", ""),
            }
        )

    primary = cards[0] if cards else {}
    bridge_message = build_counselor_bridge_message(user_story, card_summaries, reading)

    return {
        "user_story": user_story.strip(),
        "spread": draw_result.get("spread"),
        "spread_label_ko": draw_result.get("spread_label_ko") or draw_result.get("spread_name"),
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
    """Opening counselor turn: unpack the spread against the client's present situation."""
    story = (user_story or "").strip()
    parts: List[str] = [
        "타로에서 나온 장면을, 지금 당신 상황에 맞춰 조금 더 세밀하게 풀어볼게요.",
        "",
    ]

    if story:
        parts.append(f"당신이 들고 온 이야기: 「{story}」")
        parts.append("")
    else:
        parts.append("방금 카드로 함께 본 마음을, 현실 장면에 맞춰 이어가 볼게요.")
        parts.append("")

    if card_summaries:
        parts.append("카드가 가리킨 결:")
        for card in card_summaries:
            pos = card.get("position") or "카드"
            name = card.get("name_ko") or card.get("name_en") or "카드"
            orient = card.get("orientation") or "정방향"
            theme = (card.get("psychology_theme") or "").strip()
            meaning = (card.get("meaning") or "").strip()
            detail = theme or meaning
            if detail:
                parts.append(f"· [{pos}] {name} ({orient}) — {detail}")
            else:
                parts.append(f"· [{pos}] {name} ({orient})")
            # One short situational hook per card when we have a story + theme/meaning
            if story and detail:
                if orient == "역방향":
                    parts.append(
                        f"  → 「{story[:40]}」 안에서, 이 힘이 막히거나 뒤집혀 느껴지는 지점일 수 있어요."
                    )
                else:
                    parts.append(
                        f"  → 「{story[:40]}」 안에서 이미 움직이고 있거나, 곧 손 뻗을 수 있는 결로 읽혀요."
                    )
        parts.append("")

    analysis = (reading.get("ai_analysis") or reading.get("summary") or "").strip()
    if analysis:
        parts.append("풀이에서 특히 당신 현실에 닿는 결:")
        parts.append(_clip(analysis, 900))
        parts.append("")

    parts.extend(
        [
            "이 카드들은 운명이 아니라, 지금 마음·관계·선택이 어떻게 얽혀 있는지 보여주는 "
            "거울에 가깝습니다. 정방향은 이미 흐르는 힘, 역방향은 막히거나 과잉·내면화된 "
            "지점을 말해 줄 때가 많아요.",
            "",
            "지금 이 장면에서 가장 선명하게 남는 한 장—또는 한 감정—이 있다면 그대로 말해 주세요. "
            "그 지점부터, 당신 현실에 맞춰 한 겹 더 깊게 이어가겠습니다.",
        ]
    )
    return "\n".join(parts)


def apply_tarot_handoff(state: ChatSessionState, handoff: Dict[str, Any]) -> Dict[str, Any]:
    state.tarot_handoff = handoff
    state.tarot_blended = True
    handoff["blend_status"] = "active"
    handoff["session_id"] = state.session_id
    # Tarot is a secular self-reflection mirror — never mix pastoral/faith mode.
    state.consultation_mode = "psychology"

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

    tarot_signals = extract_tarot_signals(handoff)
    if tarot_signals:
        state.quant_features["tarot_spectrum_signals"] = tarot_signals
        top_spectrum = max(tarot_signals.items(), key=lambda item: item[1])
        state.quant_features["tarot_primary_spectrum"] = top_spectrum[0]
        state.quant_features["tarot_primary_spectrum_score"] = round(top_spectrum[1], 2)

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
    analysis = _clip((handoff.get("ai_analysis") or "").strip(), 1200)

    return (
        "\n\n## 타로 → 마음대화 · 깊은 상황 연동 (방금 전 타로 리딩과 연결)\n"
        f"내담자 현상황/질문: {handoff.get('user_story') or '미입력'}\n"
        f"스프레드: {handoff.get('spread_label_ko') or handoff.get('spread')}\n"
        "뽑힌 카드(위치·방향·의미):\n"
        + "\n".join(card_lines)
        + "\n\n풀이 요약: "
        + (handoff.get("reading_summary") or "")
        + ("\n선행 풀이(참고):\n" + analysis if analysis else "")
        + "\n\n상담 지침:\n"
        "- 매 응답에서 카드 상징을 추상적으로만 나열하지 말고, 내담자의 현상황·관계·감정·선택에 "
        "구체적으로 연결해 깊게·세밀하게 풀어 주세요.\n"
        "- 위치(과거/현재/미래·도전 등)와 정/역방향을 구분해, 지금 무엇이 흐르고 무엇이 "
        "막혀 있는지 현실적으로 말해 주세요.\n"
        "- 카드 간 상호작용(긴장·보완·반복 테마)을 읽어, 한 장의 의미만으로 끝내지 마세요.\n"
        "- 예언·확정 운세·진단·병명 단정은 금지. 자기성찰·선택·관계 패턴의 거울로 둡니다.\n"
        "- 미래 위치는 ‘정해진 결과’가 아니라 가능성과 지금 선택이 여는 방향으로 말합니다.\n"
        "- 내담자가 한 장·한 감정을 집으면 그 지점을 우선 깊게 파고, 나머지 카드는 배경으로 엮습니다.\n"
        "- 필요하면 부드러운 질문 1개로 현실 장면을 더 구체화한 뒤, 카드 언어로 다시 되비춥니다.\n"
        "- 말투는 따뜻하고 구체적. 상황 → 카드 → 의미 → 다음 한 걸음 순으로 정리합니다.\n"
        "- **타로×신앙 분리 (필수):** 성경 구절·묵상 초대·기도·목회 설교·신앙 언어로 "
        "카드를 풀지 마세요. 타로는 심리·자기성찰·관계 패턴의 은유 거울로만 둡니다. "
        "신앙·묵상 상담이 필요하면 타로 블렌드와 별도 모드에서만 다룹니다.\n"
        "- 아래 제안이 있으면 부담 없이 1개만 자연스럽게:\n"
        + (action_text or "  · (없음)")
    )


def should_suggest_tarot(state: ChatSessionState) -> bool:
    from app.services.association_licensing import feature_enabled

    if state.org_entitlements and not feature_enabled("tarot_bridge", state.org_entitlements):
        return False
    if state.tarot_blended or state.tarot_handoff:
        return False
    if state.counseling_phase not in {"conceptualization", "intervention"}:
        return False
    return state.turn_count >= 3
