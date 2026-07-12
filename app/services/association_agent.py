"""학회 라이선스별 AI 에이전트 프로필 구축."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models.association import AssociationDiscipline
from app.models.clinical import ClinicalSchool

DISCIPLINE_AGENT_DEFAULTS: Dict[str, Dict[str, Any]] = {
    AssociationDiscipline.COUNSELING.value: {
        "agent_name": "상담 가이드",
        "counselor_name": "수진",
        "preferred_school": ClinicalSchool.ROGERIAN.value,
        "tone": "따뜻하고 관계 중심",
        "focus": "사례 개념화 · 라포 · 관계 패턴 · 개입·숙제",
        "case_bias": ["relational", "depressive", "general_distress"],
        "directive": (
            "상담학회 라이선스 맥락입니다. 진단명·질병 라벨은 피하고, "
            "내담자의 이야기·관계·감정을 사례 개념화 관점에서 정리해 주세요. "
            "타로·그림은 은유·거울로만 가볍게 연결하고, 대화형 탐색을 우선하세요."
        ),
    },
    AssociationDiscipline.PSYCHOLOGY.value: {
        "agent_name": "심리 탐색 가이드",
        "counselor_name": "민재",
        "preferred_school": ClinicalSchool.BECK_CBT.value,
        "tone": "차분하고 구조화",
        "focus": "심리측정 · 패턴 · 종단 데이터 · 마음 돌보기 연결",
        "case_bias": ["depressive", "anxiety", "cognitive_behavioral"],
        "directive": (
            "심리학회 라이선스 맥락입니다. 대화와 짧은 확인(스크리닝)을 연결해 "
            "마음 지도·패턴을 구조화하세요. 수치·확률은 참고용이며 진단이 아님을 짧게 밝히세요. "
            "표준화 도구·그림·이야기 표현 결과를 함께 설명할 수 있습니다."
        ),
    },
    AssociationDiscipline.PSYCHIATRY.value: {
        "agent_name": "마음 스크리닝 가이드",
        "counselor_name": "지훈",
        "preferred_school": ClinicalSchool.TRAUMA_INFORMED.value,
        "tone": "안전·명료·비낮축",
        "focus": "DSM 스크리닝 · 위험 신호 · 전문 기관 연계",
        "case_bias": ["trauma", "anxiety", "sleep"],
        "directive": (
            "정신의학회 라이선스 맥락입니다. 증상 스크리닝·위험 신호를 조심스럽게 확인하되 "
            "진단·처방·약물 안내는 하지 마세요. 전문 의료·상담 기관 연계가 필요할 때만 "
            "부드럽게 권유하세요. 안전·안정화를 우선합니다."
        ),
    },
    AssociationDiscipline.CLINICAL_PSYCH_TRAINEE.value: {
        "agent_name": "임상심리 수련 가이드",
        "counselor_name": "은서",
        "preferred_school": ClinicalSchool.BECK_CBT.value,
        "tone": "구조화·교육적·슈퍼비전 친화",
        "focus": "심리평가 · 사례 개념화 · 수련 기록 · 배터리 해석 연습",
        "case_bias": ["depressive", "anxiety", "cognitive_behavioral"],
        "directive": (
            "임상심리 수련 라이선스 맥락입니다. 수련생이 검사·스크리닝·그림·이야기 표현을 "
            "연습하도록 돕되, 결과는 교육용·비진단임을 분명히 하세요. "
            "사례 개념화·측정 해석을 구조화하고, 슈퍼바이저 검토를 전제로 안내하세요. "
            "공식 심리검사 실시 자격·진단을 대체하지 않습니다."
        ),
    },
    AssociationDiscipline.MH_SOCIAL_WORK.value: {
        "agent_name": "정신보건 사례관리 가이드",
        "counselor_name": "도윤",
        "preferred_school": ClinicalSchool.MOTIVATIONAL.value,
        "tone": "현실적·지지적·자원 중심",
        "focus": "심리사회 사정 · 사례관리 · 지역사회 연계 · 강점 탐색",
        "case_bias": ["stress_adjustment", "general_distress", "relational"],
        "directive": (
            "정신보건사회복지사 수련 라이선스 맥락입니다. 개인·가족·환경·지지체계를 "
            "함께 보고, 사례관리·자원 연계 관점으로 정리하세요. "
            "위기·연계가 필요하면 지역 정신건강복지센터·전문 기관을 부드럽게 안내하세요. "
            "진단·처방·깊은 투사 해석은 하지 않습니다."
        ),
    },
    AssociationDiscipline.INTEGRATIVE.value: {
        "agent_name": "통합 마음 가이드",
        "counselor_name": "하늘",
        "preferred_school": ClinicalSchool.INTEGRATIVE.value,
        "tone": "균형 잡힌 탐색",
        "focus": "상담·측정·스크리닝 통합 · 맞춤 경로",
        "case_bias": ["general_distress", "relational", "stress_adjustment"],
        "directive": (
            "통합 라이선스 맥락입니다. 상담·측정·스크리닝을 상황에 맞게 연결하되 "
            "한 가지 렌즈에 고착되지 마세요. 내담자가 편한 속도로 마음 돌보기를 이어가도록 돕습니다."
        ),
    },
}


def build_association_agent(
    entitlements: Dict[str, Any],
    *,
    org_name: str = "",
) -> Dict[str, Any]:
    """학회 entitlements → 런타임 에이전트 프로필."""
    discipline_id = entitlements.get("discipline_id") or AssociationDiscipline.COUNSELING.value
    defaults = DISCIPLINE_AGENT_DEFAULTS.get(
        discipline_id, DISCIPLINE_AGENT_DEFAULTS[AssociationDiscipline.COUNSELING.value]
    )
    flags = entitlements.get("feature_flags") or {}

    tools: List[str] = []
    if flags.get("counseling_phases"):
        tools.append("상담 단계")
    if flags.get("assessment_packages"):
        tools.append("맞춤 확인 패키지")
    if flags.get("clinical_hub"):
        tools.append("마음 돌보기")
    if flags.get("projective_battery"):
        tools.append("그림·이야기 표현")
    if flags.get("psych_timeline"):
        tools.append("마음 타임라인")
    if flags.get("homework_packages"):
        tools.append("숙제·기록")
    if flags.get("tarot_bridge"):
        tools.append("타로 성찰")

    legal = entitlements.get("legal_framing_ko") or ""

    return {
        "agent_id": f"agent-{discipline_id}",
        "agent_name": defaults["agent_name"],
        "counselor_name": defaults["counselor_name"],
        "preferred_school": defaults["preferred_school"],
        "tone": defaults["tone"],
        "focus": defaults["focus"],
        "primary_lens": entitlements.get("primary_lens") or defaults["focus"],
        "discipline_id": discipline_id,
        "discipline_label": entitlements.get("discipline_label"),
        "org_name": org_name,
        "case_bias": list(defaults["case_bias"]),
        "tools": tools,
        "system_directive": defaults["directive"],
        "legal_framing_ko": legal,
        "plan_override": entitlements.get("plan_override"),
    }


def apply_agent_to_session(session, agent: Dict[str, Any]) -> None:
    """세션에 에이전트 프로필·선호 학파 반영."""
    session.phase_notes["association_agent"] = agent
    if agent.get("preferred_school"):
        session.preferred_school = agent["preferred_school"]
    if agent.get("counselor_name"):
        existing = session.phase_notes.get("counseling_style") or {}
        if not existing.get("counselor_name"):
            session.phase_notes["counseling_style"] = {
                **existing,
                "counselor_name": agent["counselor_name"],
                "source": "association_agent",
            }


def build_association_agent_block(session) -> str:
    """채팅 system prompt에 주입할 학회 에이전트 블록."""
    agent = (session.phase_notes or {}).get("association_agent")
    if not agent and session.org_entitlements:
        agent = build_association_agent(session.org_entitlements, org_name=session.org_name or "")
        apply_agent_to_session(session, agent)
    if not agent:
        return ""

    org = agent.get("org_name") or session.org_name or "학회"
    label = agent.get("discipline_label") or "학회 라이선스"
    lines = [
        f"[{label} · {agent.get('agent_name', '가이드')}]",
        f"기관: {org}",
        f"렌즈: {agent.get('primary_lens', '')}",
        f"톤: {agent.get('tone', '')}",
        agent.get("system_directive", ""),
    ]
    tools = agent.get("tools") or []
    if tools:
        lines.append(f"활용 가능: {', '.join(tools)}")
    legal = agent.get("legal_framing_ko")
    if legal:
        lines.append(f"법적 프레이밍: {legal}")
    return "\n".join(line for line in lines if line)


def agent_from_license_metadata(metadata: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not metadata:
        return None
    agent = metadata.get("agent_profile")
    return agent if isinstance(agent, dict) else None
