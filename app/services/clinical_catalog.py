"""임상심리 검사 통합 카탈로그 — 표준화·투영·학파별 총정리."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.assessments import ALL_INSTRUMENTS, ASSESSMENT_DOMAINS, INSTRUMENT_PROFILES
from app.assessments.base import ResponseType
from app.assessments.projective_battery import PROJECTIVE_INSTRUMENTS, projective_battery_catalog
from app.assessments.user_voice import INSTRUMENT_USER_VOICE, enrich_assessment_payload, user_instrument_title
from app.services.assessment_battery import build_battery_status
from app.services.assessment_directing import build_assessment_directing
from app.services.clinical_user_voice import HUB, TRACKS as USER_TRACKS, apply_user_voice_to_catalog, friendly_domain_label
from app.services.consumer_guided import guided_catalog_slice
from app.services.persistence import load_latest_session_for_user
from app.services.picture_assessment import STORE_KEY, picture_assessment_results


TRACKS = {
    "screening": {
        "track_id": "screening",
        "label": USER_TRACKS["screening"]["label"],
        "school": "정신의학·DSM·CBT·행동·인본",
        "description": USER_TRACKS["screening"]["description"],
        "route": "/clinical#screening",
        "submit_api": "/api/v1/assessments/submit",
    },
    "projective": {
        "track_id": "projective",
        "label": USER_TRACKS["projective"]["label"],
        "school": "그림·상상·이야기 표현",
        "description": USER_TRACKS["projective"]["description"],
        "route": "/picture-assessment",
        "submit_api": "/api/v1/picture-assessment/submit",
    },
}


def _formal_item_payload(instrument_id: str, item) -> Dict[str, Any]:
    base = {
        "instrument": instrument_id,
        "item_id": item.item_id,
        "prompt": item.prompt,
        "framing": item.conversational_framing,
        "response_type": item.response_type.value,
        "options": list(item.options),
    }
    return enrich_assessment_payload(base)


def build_formal_instrument(instrument_id: str) -> Dict[str, Any]:
    instrument = ALL_INSTRUMENTS[instrument_id]
    profile = INSTRUMENT_PROFILES.get(instrument_id, {})
    domain_id = profile.get("domain", "")
    domain = ASSESSMENT_DOMAINS.get(domain_id, {})
    voice = INSTRUMENT_USER_VOICE.get(instrument_id, {})
    items = [_formal_item_payload(instrument_id, item) for item in instrument.items()]
    directing = build_assessment_directing(instrument_id, item_index=0, total_items=len(items), completed=False)
    return {
        "instrument_id": instrument_id,
        "track": "screening",
        "display_name": profile.get("display_name", instrument.display_name),
        "user_title": user_instrument_title(instrument_id) or instrument.display_name,
        "domain_id": domain_id,
        "domain_label": domain.get("label"),
        "school": domain.get("school"),
        "focus": profile.get("focus"),
        "intro": voice.get("intro", ""),
        "item_count": len(items),
        "items": items,
        "directing": directing,
        "directing_rail": directing.get("rail") or [],
        "efficacy_preview": directing["layers"]["efficacy"],
    }


def unified_clinical_catalog(entitlements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    formal = [build_formal_instrument(iid) for iid in ALL_INSTRUMENTS.keys()]
    projective = projective_battery_catalog()
    formal_items = sum(f["item_count"] for f in formal)
    proj_items = projective["total_items"]

    domains: List[Dict[str, Any]] = []
    for domain_id, meta in ASSESSMENT_DOMAINS.items():
        domains.append(
            {
                "domain_id": domain_id,
                "label": meta["label"],
                "user_label": friendly_domain_label(domain_id, meta["label"]),
                "school": meta["school"],
                "instruments": meta["instruments"],
                "track": "screening",
            }
        )
    for inst in PROJECTIVE_INSTRUMENTS.values():
        if inst.instrument_id in {"htp", "sct"}:
            continue
        domains.append(
            {
                "domain_id": f"projective_{inst.instrument_id}",
                "label": inst.display_name,
                "school": inst.school,
                "instruments": [inst.instrument_id],
                "track": "projective",
                "clinical_reference": inst.clinical_reference,
            }
        )

    catalog = {
        "catalog_id": "unified_clinical_psychology",
        "title": HUB["title"],
        "subtitle": HUB["subtitle"],
        "tab_label": HUB["tab_label"],
        "disclaimer": HUB["disclaimer"],
        "tracks": list(TRACKS.values()),
        "domains": domains,
        "formal_instruments": formal,
        "projective_instruments": projective["instruments"],
        "counts": {
            "formal_instruments": len(formal),
            "projective_instruments": projective["instrument_count"],
            "unique_instruments": len(formal) + projective["instrument_count"] - 2,
            "formal_items": formal_items,
            "projective_items": proj_items,
            "total_items": formal_items + proj_items,
            "domains": len(domains),
        },
        "schools": sorted(
            {
                d.get("school", "")
                for d in domains
            }
            | {t["school"] for t in TRACKS.values()}
        ),
    }
    from app.services.association_licensing import filter_catalog_by_entitlements

    catalog = apply_user_voice_to_catalog(catalog)
    if entitlements:
        entitlements = dict(entitlements)
        if entitlements.get("org_name"):
            catalog.setdefault("license", {})["org_name"] = entitlements.get("org_name")
        catalog = filter_catalog_by_entitlements(catalog, entitlements)
        catalog = apply_user_voice_to_catalog(catalog)
    catalog["guided"] = guided_catalog_slice(catalog.get("formal_instruments") or [])
    return catalog

def build_user_clinical_summary(user_id: str) -> Dict[str, Any]:
    session = load_latest_session_for_user(user_id)
    entitlements = session.org_entitlements if session else None
    catalog = unified_clinical_catalog(entitlements)
    formal_progress: Dict[str, Any] = {}
    formal_scores: Dict[str, Any] = {}
    battery = None

    if session:
        battery = build_battery_status(session)
        for instrument_id, answers in (session.formal_answers or {}).items():
            if instrument_id not in ALL_INSTRUMENTS:
                continue
            total = len(ALL_INSTRUMENTS[instrument_id].items())
            formal_progress[instrument_id] = {
                "answered": len(answers),
                "total": total,
                "completion_rate": round(len(answers) / total, 2) if total else 0.0,
            }
            if answers:
                formal_scores[instrument_id] = ALL_INSTRUMENTS[instrument_id].score_partial(answers)

    projective_summary = None
    if session:
        store = (session.quant_features or {}).get(STORE_KEY) or {}
        if store.get("answers"):
            projective_summary = picture_assessment_results(session)

    formal_answered = sum(p.get("answered", 0) for p in formal_progress.values())
    proj_answered = (projective_summary or {}).get("answered_items", 0)

    return {
        "user_id": user_id,
        "session_id": session.session_id if session else None,
        "counts": catalog["counts"],
        "formal_progress": formal_progress,
        "formal_scores": formal_scores,
        "battery": battery,
        "projective_summary": projective_summary,
        "overall": {
            "formal_answered_items": formal_answered,
            "projective_answered_items": proj_answered,
            "total_answered_items": formal_answered + proj_answered,
            "total_catalog_items": catalog["counts"]["total_items"],
            "completion_rate": round(
                (formal_answered + proj_answered) / max(1, catalog["counts"]["total_items"]),
                2,
            ),
        },
    }
