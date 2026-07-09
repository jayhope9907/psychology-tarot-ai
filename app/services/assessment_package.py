from __future__ import annotations

from typing import Any, Dict, List
from uuid import uuid4

from app.assessments import ALL_INSTRUMENTS, ASSESSMENT_DOMAINS, INSTRUMENT_PROFILES
from app.services.case_preview import build_case_preview
from app.services.assessment_selector import _conversation_text, _score_instrument
from app.services.chat_session import ChatSessionState

PACKAGE_TIERS: Dict[str, Dict[str, Any]] = {
    "essential": {
        "label": "핵심 스크리닝",
        "description": "주호소 중심 3개 검사 · 약 8~12분",
        "max_instruments": 3,
        "price_krw": 9900,
        "price_label": "9,900원",
    },
    "standard": {
        "label": "표준 마음 종합",
        "description": "정서·관계·스트레스 5개 검사 · 약 15~20분",
        "max_instruments": 5,
        "price_krw": 14900,
        "price_label": "14,900원",
    },
    "comprehensive": {
        "label": "심층 마음 지도",
        "description": "12영역 종합 7개 검사 · 약 25~30분",
        "max_instruments": 7,
        "price_krw": 19900,
        "price_label": "19,900원",
    },
}

INSTRUMENT_LABELS_KO = {
    "phq9": "PHQ-9 · 우울 척도",
    "gad7": "GAD-7 · 불안 척도",
    "isi": "ISI · 수면 척도",
    "pss": "PSS · 스트레스 척도",
    "pcl5": "PCL-5 · 외상 스트레스",
    "rses": "RSES · 자존감",
    "attachment_ecr": "ECR · 애착·관계",
    "cbt_thought": "CBT · 인지 패턴",
    "psychodynamic": "정신동역학 · 반복 패턴",
    "behavioral": "행동 활성화 · 회피",
    "micro_emotion": "감정 온도 · 전반 기분",
    "htp": "HTP · 투사 검사",
    "tarot_reflect": "타로 · 상징 탐색",
}

PROCESS_TIMELINE_TEMPLATE: List[Dict[str, str]] = [
    {
        "step_id": "rapport_done",
        "title": "관계 형성 완료",
        "description": "안전한 대화 공간과 신뢰가 형성되었습니다.",
        "status": "done",
    },
    {
        "step_id": "package_review",
        "title": "맞춤 검사 패키지 안내",
        "description": "주호소에 맞는 검사 구성과 진행 방식을 확인합니다.",
        "status": "current",
    },
    {
        "step_id": "payment",
        "title": "결제",
        "description": "선택한 패키지 결제 후 검사가 잠금 해제됩니다.",
        "status": "pending",
    },
    {
        "step_id": "micro_tests",
        "title": "대화 속 마이크로 검사",
        "description": "상담 흐름을 끊지 않고 짧은 질문으로 하나씩 진행합니다.",
        "status": "pending",
    },
    {
        "step_id": "insight_report",
        "title": "결과 종합 · 안내",
        "description": "정상 범주 / 상담 권장 / 병원 평가 필요성을 확률로 안내합니다.",
        "status": "pending",
    },
    {
        "step_id": "counseling_continue",
        "title": "사례 개념화 → 상담 개입",
        "description": "검사 결과를 바탕으로 목표 설정과 변화를 함께 이어갑니다.",
        "status": "pending",
    },
]


def _rank_instruments(state: ChatSessionState, user_message: str) -> List[Dict[str, Any]]:
    text = _conversation_text(state, user_message)
    chief = (state.phase_notes.get("chief_complaint") or "").lower()
    combined = f"{text}\n{chief}"

    ranked: List[Dict[str, Any]] = []
    for instrument_id, profile in INSTRUMENT_PROFILES.items():
        if instrument_id not in ALL_INSTRUMENTS:
            continue
        score = _score_instrument(instrument_id, combined)
        if score <= 0 and instrument_id == "micro_emotion":
            score = 0.5
        domain_id = profile.get("domain", "")
        domain = ASSESSMENT_DOMAINS.get(domain_id, {})
        ranked.append(
            {
                "instrument_id": instrument_id,
                "display_name": INSTRUMENT_LABELS_KO.get(instrument_id, profile.get("display_name", instrument_id)),
                "domain_label": domain.get("label", ""),
                "school": domain.get("school", ""),
                "focus": profile.get("focus", ""),
                "score": round(score, 2),
                "item_count": len(ALL_INSTRUMENTS[instrument_id].items()),
                "estimated_minutes": max(2, min(5, len(ALL_INSTRUMENTS[instrument_id].items()) // 2)),
            }
        )

    ranked.sort(key=lambda row: (-row["score"], row["instrument_id"]))
    return ranked


def _pick_tier(instrument_count: int) -> str:
    if instrument_count <= 3:
        return "essential"
    if instrument_count <= 5:
        return "standard"
    return "comprehensive"


def build_assessment_package(state: ChatSessionState, user_message: str = "") -> Dict[str, Any]:
    ranked = _rank_instruments(state, user_message)
    top_scores = [row for row in ranked if row["score"] > 0][:7]
    if len(top_scores) < 3:
        fallback_ids = ["phq9", "gad7", "micro_emotion", "pss", "attachment_ecr"]
        seen = {row["instrument_id"] for row in top_scores}
        for instrument_id in fallback_ids:
            if instrument_id in seen:
                continue
            profile = INSTRUMENT_PROFILES.get(instrument_id, {})
            domain = ASSESSMENT_DOMAINS.get(profile.get("domain", ""), {})
            top_scores.append(
                {
                    "instrument_id": instrument_id,
                    "display_name": INSTRUMENT_LABELS_KO.get(instrument_id, instrument_id),
                    "domain_label": domain.get("label", ""),
                    "school": domain.get("school", ""),
                    "focus": profile.get("focus", ""),
                    "score": 0.1,
                    "item_count": len(ALL_INSTRUMENTS[instrument_id].items()),
                    "estimated_minutes": max(2, min(5, len(ALL_INSTRUMENTS[instrument_id].items()) // 2)),
                }
            )
            if len(top_scores) >= 5:
                break

    tier_id = _pick_tier(len(top_scores))
    tier = PACKAGE_TIERS[tier_id]
    selected = top_scores[: tier["max_instruments"]]
    total_minutes = sum(item["estimated_minutes"] for item in selected)

    timeline = [dict(step) for step in PROCESS_TIMELINE_TEMPLATE]

    instrument_steps = [
        {
            "order": index,
            "instrument_id": item["instrument_id"],
            "title": item["display_name"],
            "subtitle": item["domain_label"],
            "focus": item["focus"],
            "estimated_minutes": item["estimated_minutes"],
            "delivery": "대화 중 1문항씩 · 부담 없이 건너뛰기 가능",
        }
        for index, item in enumerate(selected, start=1)
    ]

    chief = state.phase_notes.get("chief_complaint") or "지금까지 나눈 마음"
    case_preview = build_case_preview(state, user_message, ranked_instruments=ranked)

    return {
        "package_id": str(uuid4()),
        "tier_id": tier_id,
        "tier_label": tier["label"],
        "tier_description": tier["description"],
        "price_krw": tier["price_krw"],
        "price_label": tier["price_label"],
        "chief_complaint": chief,
        "case_preview": case_preview,
        "recommended_instruments": selected,
        "instrument_steps": instrument_steps,
        "total_instruments": len(selected),
        "estimated_duration_minutes": total_minutes,
        "process_timeline": timeline,
        "disclaimer": (
            "본 검사는 의료 진단이 아닌 참고용 스크리닝입니다. "
            "결과는 대화와 함께 누적되며, 정상 범주·상담·병원 평가 필요성을 확률로 안내합니다."
        ),
        "payment_required": not state.assessment_paid,
    }


def mark_package_presented(state: ChatSessionState, package: Dict[str, Any]) -> None:
    state.assessment_package = package
    state.assessment_package_ready = True


def complete_checkout(state: ChatSessionState, tier_id: str | None = None) -> Dict[str, Any]:
    package = state.assessment_package or build_assessment_package(state)
    if tier_id and tier_id in PACKAGE_TIERS:
        tier = PACKAGE_TIERS[tier_id]
        ranked = _rank_instruments(state, "")
        selected = ranked[: tier["max_instruments"]]
        package = build_assessment_package(state)
        package["tier_id"] = tier_id
        package["recommended_instruments"] = selected
        package["instrument_steps"] = [
            {
                "order": index,
                "instrument_id": item["instrument_id"],
                "title": item["display_name"],
                "subtitle": item["domain_label"],
                "focus": item["focus"],
                "estimated_minutes": item["estimated_minutes"],
                "delivery": "대화 중 1문항씩 · 부담 없이 건너뛰기 가능",
            }
            for index, item in enumerate(selected, start=1)
        ]
        package["price_krw"] = tier["price_krw"]
        package["price_label"] = tier["price_label"]
        package["tier_label"] = tier["label"]
        package["total_instruments"] = len(selected)
        state.assessment_package = package

    payment_id = f"pay_{uuid4().hex[:12]}"
    state.assessment_paid = True
    state.payment_id = payment_id
    state.counseling_phase = "assessment"

    if not state.phase_history or state.phase_history[-1] != "assessment":
        state.phase_history.append("assessment")

    return {
        "success": True,
        "payment_id": payment_id,
        "paid": True,
        "amount_krw": package.get("price_krw", 0),
        "tier_label": package.get("tier_label", ""),
        "message": "결제가 완료되었습니다. 이제 대화 속 검사를 시작할 수 있어요.",
    }
