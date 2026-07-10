from __future__ import annotations

from typing import Any, Dict, List, Optional

SERVICE_NAME = "마음쉼터"
SERVICE_TYPE = "ai_wellness_self_reflection"

CRISIS_KEYWORDS: tuple[str, ...] = (
    "자살",
    "자해",
    "죽고 싶",
    "죽을까",
    "죽고싶",
    "목숨",
    "뛰어내",
    "손목",
    "약을 많이",
    "더 이상 못",
    "삭제하고 싶",
    "해치고 싶",
    "죽어야",
    "죽어버",
    "끝내고 싶",
    "생을",
    "극단적",
)

CRISIS_RESOURCES: List[Dict[str, str]] = [
    {"label": "자살예방 상담전화", "number": "1393", "note": "24시간"},
    {"label": "응급", "number": "119", "note": "생명 위험 시"},
    {"label": "정신건강 위기상담", "number": "129", "note": "보건복지부"},
    {"label": "청소년 전화", "number": "1577-0199", "note": "청소년·학부모"},
]

SERVICE_SCOPE_SUMMARY = (
    "마음쉼터는 AI 기반 마음 웰니스·자기성찰 도구입니다. "
    "정신과 진료, 의료행위, 임상심리치료, 진단·처방을 제공하지 않으며, "
    "면허를 가진 의료인·상담사를 대체하지 않습니다."
)


def detect_crisis(message: str) -> bool:
    text = (message or "").lower().strip()
    if not text:
        return False
    return any(keyword in text for keyword in CRISIS_KEYWORDS)


def build_crisis_reply() -> str:
    lines = [
        "지금 정말 힘든 마음이 전해져요. 혼자 버티지 않으셔도 돼요.",
        "",
        "⚠️ **중요:** 이 서비스는 응급·의료·정신과 진료 서비스가 **아닙니다.**",
        "즉시 아래 전문 기관에 연락해 주세요.",
        "",
    ]
    for item in CRISIS_RESOURCES:
        lines.append(f"• **{item['label']} {item['number']}** ({item['note']})")
    lines.extend(
        [
            "",
            "전문 의료·상담 기관의 도움을 받으시는 것이 가장 안전합니다.",
            "원하시면 지금 느끼는 마음을 천천히 적어 주셔도 괜찮아요. "
            "다만 위급하면 반드시 전화로 도움을 요청해 주세요.",
        ]
    )
    return "\n".join(lines)


def build_legal_system_block() -> str:
    return (
        "## [법적·서비스 범위 — 반드시 준수]\n"
        f"- 서비스: **{SERVICE_NAME}** — AI 기반 **마음 웰니스·자기성찰·감정 정리** 도구\n"
        "- **하지 않는 것:** 정신과 진료, 의료행위, 임상심리치료, 질병·장애 **진단**, "
        "약물·치료 **처방**, 응급 개입, 면허 상담/치료 대체\n"
        "- **AI 생성 응답**임을 필요 시 명시. 면허 전문가가 아님\n"
        "- 질환명·진단명 **단정 금지** (\"~일 수 있어요\", \"참고용\"만)\n"
        "- 병원·정신과 방문 **필요 여부 단정 금지**. "
        "\"전문 기관 상담을 **고려**해 볼 수 있어요\" 수준만\n"
        "- 위기(자해·자살·타해) 시: 1393, 119, 129, 1577-0199 안내. "
        "치료·진단 조언 대신 **즉시 전문 도움** 권고\n"
        "- 타로·검사·패턴 분석은 **자기 이해 참고용**이며 의료 판단이 아님"
    )


def build_consent_document() -> Dict[str, Any]:
    return {
        "service_name": SERVICE_NAME,
        "service_type": SERVICE_TYPE,
        "version": "1.0",
        "summary": SERVICE_SCOPE_SUMMARY,
        "acknowledgments": [
            "본 서비스는 AI가 생성하는 웰니스·자기성찰 대화이며, 의료·정신과 진료·응급 서비스가 아닙니다.",
            "AI 응답은 참고용이며, 진단·치료·약물 처방을 대체하지 않습니다.",
            "위기 상황(자해·자살·타해 등)에서는 1393·119·129 등 전문 기관에 즉시 연락해야 합니다.",
            "유료 마음 체크·패키지는 참고용 스크리닝이며 의료 진단이 아닙니다.",
            "대화 내용은 서비스 개선·세션 유지 목적으로 저장될 수 있습니다.",
        ],
        "crisis_resources": CRISIS_RESOURCES,
        "legal_links": {
            "terms": "/legal#terms",
            "privacy": "/legal#privacy",
            "disclaimer": "/legal#disclaimer",
        },
    }


def reframe_clinical_label(text: str) -> str:
    """User-facing copy: avoid medical/hospital framing."""
    replacements = {
        "전문 상담·검사 권장 가능성": "마음 상태 참고 지표",
        "병원·상담이 필요한지": "전문 기관 상담을 고려할 여지",
        "정신과": "전문 의료",
        "진단": "참고 분류",
        "상담심리 전문가": "AI 웰니스 가이드",
        "임상심리 상담사": "AI 마음 가이드",
        "상담사": "AI 가이드",
        "병원·전문기관": "전문 의료·상담 기관",
        "전문 상담·검사": "전문 기관 상담·참고 체크",
        "심리검사": "마음 체크",
    }
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


def reframe_insight_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    reframed = dict(payload)
    for key in ("overall_zone_label", "recommendation_label", "summary_ko", "disclaimer"):
        if reframed.get(key):
            reframed[key] = reframe_clinical_label(str(reframed[key]))
    reframed["care_reference_label"] = "전문 기관 상담 고려 지표"
    return reframed
