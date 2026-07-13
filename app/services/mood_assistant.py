from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.services.chat_session import ChatSessionState
from app.services.counseling_phase import (
    PHASE_ASSESSMENT_BRIEFING,
    PHASE_RAPPORT,
)
from app.services.daily_routine import MOOD_LABELS, today_checkin
from app.services.fatigue_manager import detect_assessment_request, detect_distress
from app.services.mood_dimensions import (
    MOOD_DIMENSION_META,
    build_agent_system_block,
    build_agent_welcome,
    build_mood_agent_profile,
    dimension_summary,
    dominant_concerns,
    normalize_dimensions,
)


@dataclass
class MoodContext:
    score: int
    label: str
    note: str
    has_checkin: bool
    dimensions: Dict[str, int] = field(default_factory=dict)
    agent: Optional[Dict[str, Any]] = None

    @classmethod
    def unknown(cls) -> "MoodContext":
        return cls(score=3, label="보통", note="", has_checkin=False, dimensions=normalize_dimensions({}))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "label": self.label,
            "note": self.note,
            "has_checkin": self.has_checkin,
            "dimensions": self.dimensions,
            "dimension_summary": dimension_summary(self.dimensions) if self.has_checkin else "",
            "agent": self.agent,
        }


MOOD_PROFILES: Dict[int, Dict[str, Any]] = {
    1: {
        "tone": "매우 부드럽고 느리게. 판단·조언·강요 없이 안전감과 위로 우선.",
        "comfort_focus": "혼자가 아니라는 느낌, 지금의 pain 인정, 호흡·쉼 허용",
        "forbidden": ["힘내세요", "긍정적으로", "별거 아니", "검사부터", "결제"],
        "min_comfort_turns": 3,
        "assessment_turn_threshold": 4,
        "recommended_tier": "essential",
        "assessment_frame": (
            "지금처럼 마음이 무거울 때는, 감정만으로 버티기보다 "
            "짧은 마음 검사로 상태를 함께 확인해 보면 혼자 견디지 않아도 돼요."
        ),
        "payment_frame": (
            "오늘처럼 힘든 날일수록, 내 마음을 숫자와 패턴으로 남겨 두면 "
            "다음 대화가 더 정확해져요. 부담 없는 핵심 패키지부터 시작할 수 있어요."
        ),
    },
    2: {
        "tone": "따뜻하고 공감적으로. 해결책보다 감정 수용을 먼저.",
        "comfort_focus": "힘듦 인정, 구체적 상황 탐색, 작은 위로",
        "forbidden": ["쉽게", "금방 나아", "결제부터"],
        "min_comfort_turns": 2,
        "assessment_turn_threshold": 3,
        "recommended_tier": "essential",
        "assessment_frame": (
            "말씀해 주신 마음을 더 정확히 이해하려면, "
            "대화와 함께 짧은 심리검사로 지금 상태를 확인해 보는 것도 도움이 돼요."
        ),
        "payment_frame": (
            "지금 상태를 기록으로 남기면, 다음 상담에서 더 깊이 이어갈 수 있어요. "
            "필요하다면 핵심 검사 패키지로 부담 없이 시작해 볼 수 있어요."
        ),
    },
    3: {
        "tone": "균형 잡힌 공감. 탐색과 안내를 함께.",
        "comfort_focus": "감정 반영 + 한 걸음 더 깊은 질문",
        "forbidden": ["무조건 검사", "지금 당장 결제"],
        "min_comfort_turns": 2,
        "assessment_turn_threshold": 3,
        "recommended_tier": "standard",
        "assessment_frame": (
            "지금 마음을 조금 더 선명하게 보려면, 맞춤 심리검사로 "
            "패턴을 함께 그려볼 수 있어요."
        ),
        "payment_frame": (
            "검사 결과가 쌓이면, 상담이 더 구체적으로 이어져요. "
            "표준 패키지면 정서·스트레스·관계를 한 번에 살펴볼 수 있어요."
        ),
    },
    4: {
        "tone": "밝고 지지적. 성장과 자기 이해 강조.",
        "comfort_focus": "긍정 강화 + 탐색",
        "forbidden": ["무겁게", "너무 salesy"],
        "min_comfort_turns": 1,
        "assessment_turn_threshold": 2,
        "recommended_tier": "standard",
        "assessment_frame": (
            "괜찮은 하루를 더 잘 이해하려면, 짧은 검사로 "
            "나만의 마음 패턴을 확인해 볼 수 있어요."
        ),
        "payment_frame": (
            "마음 지도를 만들어 두면, 앞으로 힘든 날에도 "
            "스스로를 더 잘 돌볼 수 있어요."
        ),
    },
    5: {
        "tone": "가볍고 활기차게. 자기 이해·성장 프레이밍.",
        "comfort_focus": "좋은 에너지 인정, 유지·확장",
        "forbidden": ["우울하", "힘들"],
        "min_comfort_turns": 1,
        "assessment_turn_threshold": 2,
        "recommended_tier": "standard",
        "assessment_frame": (
            "좋은 흐름을 이어가려면, 마음 검사로 "
            "지금의 강점과 주의할 패턴을 함께 볼 수 있어요."
        ),
        "payment_frame": (
            "종합 검사로 마음의 큰 그림을 그려 두면, "
            "앞으로의 선택에도 도움이 돼요."
        ),
    },
}


def resolve_mood_context(user_id: str) -> MoodContext:
    checkin = today_checkin(user_id)
    if not checkin:
        return MoodContext.unknown()
    dims = normalize_dimensions(checkin.get("dimensions") or {})
    agent = checkin.get("agent") or build_mood_agent_profile(dims, checkin["mood_score"]).to_dict()
    return MoodContext(
        score=int(checkin["mood_score"]),
        label=checkin.get("mood_label") or MOOD_LABELS.get(int(checkin["mood_score"]), "보통"),
        note=(checkin.get("note") or "").strip(),
        has_checkin=True,
        dimensions=dims,
        agent=agent,
    )


def _profile(ctx: MoodContext) -> Dict[str, Any]:
    return MOOD_PROFILES.get(ctx.score, MOOD_PROFILES[3])


def build_mood_mandatory_system_block(ctx: MoodContext, state: ChatSessionState) -> str:
    profile = _profile(ctx)
    lines = [
        "## [필수] 오늘 기분 맞춤 상담 규칙",
        "내담자의 **오늘 입체 체크인(5축)** 에 무조건 맞춰 대화하세요.",
    ]
    if ctx.has_checkin:
        lines.append(f"- 종합 기분: **{ctx.score}/5 ({ctx.label})**")
        lines.append(f"- 입체 좌표: {dimension_summary(ctx.dimensions)}")
        if ctx.note:
            lines.append(f'- 체크인 메모: "{ctx.note}"')
        if ctx.agent:
            lines.append(build_agent_system_block(build_mood_agent_profile(ctx.dimensions, ctx.score)))
        else:
            lines.append(f"- 말투·속도: {profile['tone']}")
            lines.append(f"- 우선 초점: {profile['comfort_focus']}")
        lines.append(f"- 금지 표현: {', '.join(profile['forbidden'])}")
    else:
        lines.append("- 오늘 체크인 기록이 없습니다. 먼저 따뜻히 환영하고, 기분을 가볍게 물어보세요.")

    if ctx.score <= 2:
        lines.extend(
            [
                "- **1~2단계**: 공감·위로·안전감만. 검사·결제·패키지 언급 금지.",
                f"- **{profile['assessment_turn_threshold']}턴 이후**: 위로가 충분하면 검사를 '돌봄'으로 자연스럽게 제안.",
                "- 결제는 패키지 카드와 함께, '부담 없는 시작' 프레이밍만.",
            ]
        )
    elif ctx.score >= 4:
        lines.extend(
            [
                "- 기분이 비교적 괜찮으므로, 자기 이해·성장 관점으로 검사를 제안할 수 있습니다.",
                "- 결제는 '마음 지도 만들기'처럼 긍정적으로 프레이밍.",
            ]
        )
    else:
        lines.extend(
            [
                "- 공감 후, 대화 흐름이 자연스러우면 검사·패키지를 부드럽게 연결.",
            ]
        )

    if state.counseling_phase == PHASE_ASSESSMENT_BRIEFING:
        lines.append(f"- 검사 안내 프레이밍: {profile['assessment_frame']}")
        lines.append(f"- 결제 안내 프레이밍: {profile['payment_frame']}")

    lines.append("- 검사·결제는 **강요하지 말고**, 내담자가 준비됐을 때 선택하도록 하세요.")
    return "\n".join(lines)


def get_mood_welcome_message(ctx: MoodContext) -> str:
    if ctx.has_checkin and ctx.agent:
        profile = build_mood_agent_profile(ctx.dimensions, ctx.score)
        return build_agent_welcome(profile, ctx.note, has_checkin=True)
    return build_agent_welcome(build_mood_agent_profile(), ctx.note, has_checkin=False)


def rapport_ready_for_assessment(state: ChatSessionState, ctx: MoodContext) -> bool:
    profile = _profile(ctx)
    min_turns = profile["min_comfort_turns"]
    if state.turn_count < min_turns:
        return False
    if ctx.has_checkin and ctx.score <= 2:
        return state.turn_count >= profile["assessment_turn_threshold"]
    if ctx.has_checkin and ctx.score >= 4:
        return state.turn_count >= 2
    return state.turn_count >= min_turns + 1


def mood_priority_reply(
    ctx: MoodContext,
    state: ChatSessionState,
    user_message: str,
    decision: Any = None,
    assessment_response: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """기분 우선 fallback — 첫 턴·저조 기분에서 공감·위로."""
    if assessment_response or (decision and getattr(decision, "action", None) == "inject_assessment"):
        return None
    if detect_assessment_request(user_message):
        return None

    profile = _profile(ctx)
    note_ref = f' "{ctx.note}"' if ctx.note else ""
    concerns = dominant_concerns(ctx.dimensions)
    concern_ref = f" {concerns[0]} 마음이" if concerns else ""

    if state.turn_count <= 1 and ctx.has_checkin:
        agent_label = (ctx.agent or {}).get("label", "")
        if ctx.score <= 2:
            return (
                f"오늘 입체 체크인을 보니{concern_ref} 느껴지시는군요.{note_ref} "
                f"{'**' + agent_label + '** 모드로 ' if agent_label else ''}"
                "지금 몸이나 마음에서 가장 크게 느껴지는 부분을 한 가지 말씀해 주실 수 있을까요?"
            )
        if ctx.score >= 4:
            return (
                f"오늘 {ctx.label}({ctx.score}/5)으로 체크인해 주셨네요.{note_ref} "
                "이 흐름 속에서 지금 나누고 싶은 이야기가 있다면 편하게 들려주세요."
            )
        return (
            f"오늘 {ctx.label}({ctx.score}/5)으로 체크인해 주셨군요.{note_ref} "
            "그 마음 그대로 받아들이며 들을게요. 지금 가장 신경 쓰이는 건 무엇인가요?"
        )

    if ctx.score <= 2 and state.turn_count <= profile["assessment_turn_threshold"]:
        if detect_distress(user_message) or any(k in user_message for k in ("힘들", "우울", "답답", "무서")):
            return (
                "말씀해 주신 마음, 정말 무겁게 느껴져요. "
                "혼자 버티지 않으셔도 돼요. "
                "그 감정이 가장 크게 올라올 때가 언제인지, 천천히 들려주실 수 있을까요?"
            )
        return (
            f"오늘 {ctx.label}한 마음을 기억하고 있어요. "
            "조급하게 가지 않을게요. 지금 가장 먼저 풀고 싶은 부분이 있다면 무엇인가요?"
        )

    return None


def should_nudge_assessment(state: ChatSessionState, ctx: MoodContext) -> bool:
    if state.assessment_paid or state.assessment_package_ready:
        return False
    if state.counseling_phase not in (PHASE_RAPPORT, PHASE_ASSESSMENT_BRIEFING):
        return False
    profile = _profile(ctx)
    return state.turn_count >= profile["assessment_turn_threshold"]


def build_assessment_soft_nudge(ctx: MoodContext, state: ChatSessionState) -> str:
    profile = _profile(ctx)
    if ctx.score <= 2:
        return (
            f" {profile['assessment_frame']} "
            "원하시면 아래에서 맞춤 검사 패키지를 미리 확인해 보실 수 있어요."
        )
    return f" {profile['assessment_frame']}"


def build_payment_soft_nudge(ctx: MoodContext, package: Optional[Dict[str, Any]] = None) -> str:
    profile = _profile(ctx)
    price = (package or {}).get("price_label", "")
    tier = (package or {}).get("tier_label", "맞춤 패키지")
    if ctx.score <= 2:
        return (
            f"\n\n{profile['payment_frame']} "
            f"({tier} · {price}) — 준비되시면 아래에서 시작하실 수 있어요."
        )
    return f"\n\n{profile['payment_frame']} ({tier} · {price})"


def maybe_append_natural_nudge(
    text: str,
    state: ChatSessionState,
    ctx: MoodContext,
) -> str:
    if not should_nudge_assessment(state, ctx):
        return text
    if state.counseling_phase == PHASE_ASSESSMENT_BRIEFING:
        return text
    nudge = build_assessment_soft_nudge(ctx, state)
    if nudge.strip() in text:
        return text
    if ctx.score <= 2 and state.turn_count < _profile(ctx)["assessment_turn_threshold"]:
        return text
    return (text.rstrip() + nudge).strip()


def enrich_package_with_mood(
    package: Dict[str, Any],
    ctx: MoodContext,
    state: ChatSessionState,
) -> Dict[str, Any]:
    profile = _profile(ctx)
    enriched = dict(package)
    enriched["mood_context"] = ctx.to_dict()
    enriched["agent"] = ctx.agent
    enriched["mood_intro"] = (
        f"오늘 입체 체크인: {dimension_summary(ctx.dimensions)}. "
        f"{(ctx.agent or {}).get('label', '')} 모드로 맞춰 드릴게요. "
        f"{profile['assessment_frame']}"
        if ctx.has_checkin
        else profile["assessment_frame"]
    )
    enriched["mood_payment_copy"] = profile["payment_frame"]
    enriched["recommended_for_mood"] = profile["recommended_tier"]
    if ctx.has_checkin and ctx.score <= 2 and enriched.get("tier_id") != "essential":
        from app.services.assessment_package import PACKAGE_TIERS

        tier = PACKAGE_TIERS["essential"]
        enriched["mood_tier_suggestion"] = {
            "tier_id": "essential",
            "tier_label": tier["label"],
            "price_label": tier["price_label"],
            "reason": "오늘 마음이 무거울 때는 부담 적은 핵심 검사부터 시작하는 것을 권장해요.",
        }
    chief = state.phase_notes.get("chief_complaint") or ctx.note or "지금까지 나눈 마음"
    enriched["chief_complaint"] = chief
    return enriched


def build_assessment_briefing_reply(ctx: MoodContext, package: Dict[str, Any]) -> str:
    intro = package.get("mood_intro") or enrich_package_with_mood(package, ctx, ChatSessionState(user_id="")).get(
        "mood_intro", ""
    )
    pay = package.get("mood_payment_copy") or _profile(ctx)["payment_frame"]
    tier = package.get("tier_label", "")
    price = package.get("price_label", "")
    return (
        f"{intro}\n\n"
        f"대화를 바탕으로 **{tier}**({price}) 패키지를 준비했어요. "
        "검사는 진단이 아니라, 지금 마음을 더 정확히 이해하기 위한 참고용이에요.\n\n"
        f"{pay}\n\n"
        "아래 카드에서 구성과 진행 과정을 확인해 보시고, "
        "준비되시면 결제 후 바로 이어서 진행할 수 있어요."
    )
