from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.assessments import ALL_INSTRUMENTS, ASSESSMENT_DOMAINS, INSTRUMENT_PROFILES
from app.assessments.base import AssessmentItem
from app.services.chat_session import ChatSessionState


def _instrument_completion(state: ChatSessionState, instrument_id: str) -> float:
    instrument = ALL_INSTRUMENTS.get(instrument_id)
    if not instrument:
        return 0.0
    answers = state.formal_answers.get(instrument_id, {})
    return instrument.score_partial(answers).get("completion_rate", 0.0)


def build_battery_status(state: ChatSessionState) -> Dict[str, Any]:
    domains: List[Dict[str, Any]] = []
    total_items = 0
    completed_items = 0

    for domain_id, meta in ASSESSMENT_DOMAINS.items():
        instrument_ids = meta["instruments"]
        instrument_status = []
        domain_complete = True

        for instrument_id in instrument_ids:
            instrument = ALL_INSTRUMENTS.get(instrument_id)
            if not instrument:
                continue
            answers = state.formal_answers.get(instrument_id, {})
            total = len(instrument.items())
            done = len(answers)
            total_items += total
            completed_items += done
            rate = round(done / total, 2) if total else 0.0
            if rate < 1.0:
                domain_complete = False
            instrument_status.append(
                {
                    "instrument_id": instrument_id,
                    "display_name": INSTRUMENT_PROFILES.get(instrument_id, {}).get("display_name", instrument_id),
                    "completion_rate": rate,
                    "partial_score": instrument.score_partial(answers) if answers else None,
                }
            )

        domains.append(
            {
                "domain_id": domain_id,
                "label": meta["label"],
                "school": meta["school"],
                "instruments": instrument_status,
                "domain_complete": domain_complete,
            }
        )

    overall = round(completed_items / total_items, 2) if total_items else 0.0
    return {
        "session_id": state.session_id,
        "turn_count": state.turn_count,
        "domains": domains,
        "domains_complete": sum(1 for d in domains if d["domain_complete"]),
        "domains_total": len(domains),
        "overall_completion_rate": overall,
        "instruments_touched": len([iid for iid in state.formal_answers if state.formal_answers[iid]]),
        "instruments_total": len(ALL_INSTRUMENTS),
    }


def _uncovered_domain_instruments(state: ChatSessionState) -> List[str]:
    untouched: List[str] = []
    for domain_id, meta in ASSESSMENT_DOMAINS.items():
        for instrument_id in meta["instruments"]:
            if not state.formal_answers.get(instrument_id):
                untouched.append(instrument_id)
    return untouched


def boost_battery_coverage_scores(
    state: ChatSessionState,
    base_scores: Dict[str, float],
) -> Dict[str, float]:
    """ROI: 아직 조사 안 된 영역에 가중치를 줘 전체 배터리를 채운다."""
    boosted = dict(base_scores)
    untouched = set(_uncovered_domain_instruments(state))

    for instrument_id in untouched:
        boosted[instrument_id] = boosted.get(instrument_id, 0.0) + 0.9

    for instrument_id, answers in state.formal_answers.items():
        if not answers:
            continue
        completion = _instrument_completion(state, instrument_id)
        if 0 < completion < 1.0:
            boosted[instrument_id] = boosted.get(instrument_id, 0.0) + 1.5

    return boosted


def next_recommended_instruments(state: ChatSessionState, limit: int = 5) -> List[Dict[str, Any]]:
    recommendations: List[Dict[str, Any]] = []
    for domain_id, meta in ASSESSMENT_DOMAINS.items():
        for instrument_id in meta["instruments"]:
            instrument = ALL_INSTRUMENTS.get(instrument_id)
            if not instrument:
                continue
            answers = state.formal_answers.get(instrument_id, {})
            next_item = instrument.next_item(answers)
            if not next_item:
                continue
            recommendations.append(
                {
                    "domain_id": domain_id,
                    "domain_label": meta["label"],
                    "school": meta["school"],
                    "instrument_id": instrument_id,
                    "next_item_id": next_item.item_id,
                    "completion_rate": _instrument_completion(state, instrument_id),
                }
            )
        if len(recommendations) >= limit:
            break
    return recommendations[:limit]


def sync_session_battery(state: ChatSessionState) -> Dict[str, Any]:
    status = build_battery_status(state)
    state.battery_coverage = {
        "overall_completion_rate": status["overall_completion_rate"],
        "domains_complete": status["domains_complete"],
        "domains_total": status["domains_total"],
        "instruments_touched": status["instruments_touched"],
        "instruments_total": status["instruments_total"],
    }
    return state.battery_coverage
