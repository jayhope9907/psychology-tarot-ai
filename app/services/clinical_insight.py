from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.assessments import ALL_INSTRUMENTS, ASSESSMENT_DOMAINS, INSTRUMENT_PROFILES
from app.services.assessment_battery import build_battery_status
from app.services.chat_session import ChatSessionState

# severity_hint → 0~1 위험 점수 (임상 스크리닝 literature 기반 근사)
SEVERITY_RISK = {
    "minimal": 0.08,
    "normal": 0.08,
    "low": 0.12,
    "healthy": 0.08,
    "secure": 0.1,
    "minimal_elevated": 0.22,
    "mild": 0.32,
    "moderate": 0.58,
    "moderately_severe": 0.7,
    "elevated": 0.48,
    "severe": 0.78,
    "screen_positive": 0.72,
    "insecure": 0.42,
    "active": 0.38,
    "withdrawn": 0.45,
    "insufficient_data": 0.0,
    "check_in": 0.15,
    "symbolic": 0.1,
    "partial": 0.18,
    "low_strength": 0.36,
    "projective_complete": 0.12,
}

CLINICAL_INSTRUMENTS = frozenset(
    {
        "phq9",
        "gad7",
        "isi",
        "pss",
        "pcl5",
    }
)

ZONE_LABELS = {
    "normal": "전반적으로 안정적인 편입니다",
    "mild_elevation": "가벼운 주의가 도움될 수 있습니다",
    "clinical_concern": "전문 기관 상담을 고려할 여지가 있습니다",
    "insufficient_data": "아직 참고하기 이릅니다",
}

RECOMMENDATION_LABELS = {
    "self_monitoring": "자가 관찰 · 생활 리듬 유지",
    "counseling_suggested": "전문 기관 상담을 고려해 볼 수 있습니다",
    "clinical_evaluation_recommended": "전문 의료·상담 기관 평가를 고려해 볼 수 있습니다",
    "urgent_care_suggested": "가까운 전문기관·위기 지원을 권장합니다",
    "continue_assessment": "참고용 체크를 조금 더 진행해 주세요",
}


def _risk_from_score(instrument_id: str, score: Dict[str, Any]) -> float:
    hint = str(score.get("severity_hint") or "insufficient_data")
    base = SEVERITY_RISK.get(hint, 0.2)

    partial = score.get("partial_score")
    if isinstance(partial, (int, float)) and instrument_id in {"phq9", "gad7", "isi", "pss", "pcl5"}:
        caps = {"phq9": 15.0, "gad7": 12.0, "isi": 9.0, "pss": 6.0, "pcl5": 6.0}
        cap = caps.get(instrument_id, 10.0)
        normalized = min(1.0, float(partial) / cap)
        base = max(base, normalized * 0.85)

    completion = float(score.get("completion_rate") or 0.0)
    if completion < 0.34:
        return base * 0.45
    if completion < 0.67:
        return base * 0.75
    return base


def _domain_findings(state: ChatSessionState) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for domain_id, meta in ASSESSMENT_DOMAINS.items():
        domain_risks: List[float] = []
        instruments: List[Dict[str, Any]] = []

        for instrument_id in meta["instruments"]:
            answers = state.formal_answers.get(instrument_id)
            if not answers:
                continue
            instrument = ALL_INSTRUMENTS.get(instrument_id)
            if not instrument:
                continue
            score = instrument.score_partial(answers)
            if score.get("severity_hint") == "insufficient_data":
                continue
            risk = _risk_from_score(instrument_id, score)
            domain_risks.append(risk)
            instruments.append(
                {
                    "instrument_id": instrument_id,
                    "display_name": INSTRUMENT_PROFILES.get(instrument_id, {}).get("display_name", instrument_id),
                    "risk_score": round(risk, 2),
                    "severity_hint": score.get("severity_hint"),
                    "completion_rate": score.get("completion_rate"),
                }
            )

        if not instruments:
            continue

        avg_risk = sum(domain_risks) / len(domain_risks)
        findings.append(
            {
                "domain_id": domain_id,
                "label": meta["label"],
                "school": meta["school"],
                "risk_score": round(avg_risk, 2),
                "instruments": instruments,
            }
        )

    findings.sort(key=lambda item: item["risk_score"], reverse=True)
    return findings


def _confidence(state: ChatSessionState, battery: Dict[str, Any]) -> float:
    overall = float(battery.get("overall_completion_rate") or 0.0)
    clinical_touched = sum(
        1
        for iid in CLINICAL_INSTRUMENTS
        if state.formal_answers.get(iid) and len(state.formal_answers[iid]) >= 2
    )
    clinical_factor = min(1.0, clinical_touched / 3.0)
    turn_factor = min(1.0, state.turn_count / 6.0)
    return round(min(0.95, overall * 0.45 + clinical_factor * 0.4 + turn_factor * 0.15), 2)


def _professional_care_probability(findings: List[Dict[str, Any]], confidence: float) -> float:
    if not findings:
        return 0.0

    risks = [item["risk_score"] for item in findings]
    top = risks[0]
    mean_top3 = sum(risks[:3]) / min(3, len(risks))
    elevated_clinical = sum(
        1
        for item in findings
        if item["domain_id"].startswith("clinical_") and item["risk_score"] >= 0.4
    )

    raw = top * 0.45 + mean_top3 * 0.3 + min(1.0, elevated_clinical / 2.0) * 0.25
    # 데이터가 적을수록 보수적으로 낮춤
    adjusted = raw * (0.55 + confidence * 0.45)
    return round(min(0.92, max(0.0, adjusted)), 2)


def _overall_zone(probability: float, confidence: float, findings: List[Dict[str, Any]]) -> str:
    if confidence < 0.22 or not findings:
        return "insufficient_data"
    if probability >= 0.55:
        return "clinical_concern"
    if probability >= 0.28:
        return "mild_elevation"
    return "normal"


def _recommendation_tier(zone: str, probability: float, findings: List[Dict[str, Any]]) -> str:
    trauma_risk = next(
        (item["risk_score"] for item in findings if item["domain_id"] == "clinical_trauma"),
        0.0,
    )
    if trauma_risk >= 0.65:
        return "urgent_care_suggested"
    if zone == "insufficient_data":
        return "continue_assessment"
    if probability >= 0.62:
        return "clinical_evaluation_recommended"
    if probability >= 0.35:
        return "counseling_suggested"
    return "self_monitoring"


def _build_summary(
    zone: str,
    probability: float,
    confidence: float,
    recommendation: str,
    findings: List[Dict[str, Any]],
) -> str:
    pct = int(round(probability * 100))
    conf_pct = int(round(confidence * 100))

    if zone == "insufficient_data":
        return (
            "아직 충분한 참고 데이터가 쌓이지 않았어요. "
            "대화를 이어가며 몇 가지 질문에 답해 주시면, "
            "마음 패턴을 웰니스 관점에서 더 정확히 안내해 드릴 수 있어요."
        )

    lead = ZONE_LABELS.get(zone, "")
    rec = RECOMMENDATION_LABELS.get(recommendation, "")
    top_domains = ", ".join(item["label"] for item in findings[:2])

    return (
        f"{lead} "
        f"전문 기관 상담을 고려할 여지는 약 {pct}%로 추정됩니다(신뢰도 {conf_pct}%). "
        f"주요 신호: {top_domains or '종합 패턴'}. "
        f"참고: {rec}. "
        "※ 본 결과는 의학적 진단이 아니며, 웰니스·스크리닝 참고용입니다."
    )


def build_clinical_insight(state: ChatSessionState) -> Dict[str, Any]:
    from app.services.legal_compliance import reframe_insight_payload

    battery = build_battery_status(state)
    findings = _domain_findings(state)
    confidence = _confidence(state, battery)
    probability = _professional_care_probability(findings, confidence)
    zone = _overall_zone(probability, confidence, findings)
    recommendation = _recommendation_tier(zone, probability, findings)

    normal_probability = round(max(0.0, 1.0 - probability - (0.15 if confidence < 0.3 else 0.05)), 2)

    return reframe_insight_payload(
        {
            "session_id": state.session_id,
            "overall_zone": zone,
            "overall_zone_label": ZONE_LABELS.get(zone, zone),
            "professional_care_probability": probability,
            "normal_range_probability": normal_probability,
            "confidence": confidence,
            "recommendation_tier": recommendation,
            "recommendation_label": RECOMMENDATION_LABELS.get(recommendation, recommendation),
            "domain_findings": findings,
            "summary_ko": _build_summary(zone, probability, confidence, recommendation, findings),
            "disclaimer": "본 분석은 참고용 자가 스크리닝 추정치이며, 의학적·임상 진단을 대체하지 않습니다.",
            "battery_completion_rate": battery.get("overall_completion_rate", 0.0),
            "ready_for_interpretation": confidence >= 0.25 and bool(findings),
        }
    )


def sync_session_insight(state: ChatSessionState) -> Dict[str, Any]:
    insight = build_clinical_insight(state)
    state.clinical_insight = insight
    return insight
