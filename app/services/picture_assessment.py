"""그림 투영검사 사이트 — 임상심리 투사검사 배터리 API."""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.assessments.projective_battery import (
    PROJECTIVE_INSTRUMENTS,
    all_projective_items,
    projective_battery_catalog,
)
from app.services.clinical_user_voice import PICTURE_HUB, PROJECTIVE_USER_VOICE, apply_user_voice_to_catalog
from app.services.projective_scoring import score_item_response, score_projective_battery

STORE_KEY = "projective_battery"


def _store(session) -> Dict[str, Any]:
    qf = session.quant_features.setdefault(STORE_KEY, {})
    qf.setdefault("answers", {})
    qf.setdefault("skipped", [])
    return qf


def _item_lookup() -> Dict[str, Dict[str, str]]:
    lookup: Dict[str, Dict[str, str]] = {}
    for item in all_projective_items():
        lookup[item.item_id] = {
            "instrument_id": item.instrument_id,
            "response_type": item.response_type.value,
        }
    return lookup


def picture_assessment_catalog(entitlements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    raw = projective_battery_catalog()
    raw["title"] = PICTURE_HUB["title"]
    raw["subtitle"] = PICTURE_HUB["subtitle"]
    raw["disclaimer"] = (
        "정답은 없어요. 편한 만큼만, 넘어가도 괜찮아요. "
        "그림 실력·말재주는 중요하지 않아요."
    )
    for inst in raw.get("instruments") or []:
        voice = PROJECTIVE_USER_VOICE.get(inst.get("instrument_id", ""), {})
        inst["user_title"] = voice.get("user_title") or inst.get("display_name")
        inst["user_intro"] = voice.get("intro") or inst.get("intro")
        inst.pop("clinical_reference", None)
        for item in inst.get("items") or []:
            item.pop("clinical_note", None)

    if entitlements:
        from app.services.association_licensing import filter_catalog_by_entitlements, feature_enabled

        if not feature_enabled("projective_battery", entitlements):
            raw["instruments"] = []
            raw["instrument_count"] = 0
            raw["total_items"] = 0
        else:
            allowed = set(entitlements.get("allowed_projective") or [])
            raw["instruments"] = [i for i in raw["instruments"] if i.get("instrument_id") in allowed]
            raw["instrument_count"] = len(raw["instruments"])
            raw["total_items"] = sum(i.get("item_count", 0) for i in raw["instruments"])
        if entitlements.get("discipline_label"):
            raw["license"] = {"discipline_label": entitlements.get("discipline_label")}
    return raw


def record_projective_response(session, payload: Dict[str, Any]) -> Dict[str, Any]:
    store = _store(session)
    instrument = str(payload.get("instrument") or "")
    item_id = str(payload.get("item_id") or "")
    skipped = bool(payload.get("skipped"))

    if skipped:
        store["skipped"].append({"instrument": instrument, "item_id": item_id})
        return {"recorded": False, "skipped": True}

    lookup = _item_lookup()
    meta = lookup.get(item_id, {})
    if not meta or meta.get("instrument_id") != instrument:
        return {"recorded": False, "error": "unknown_item"}

    from app.services.association_licensing import projective_allowed

    if session.org_entitlements and not projective_allowed(instrument, session.org_entitlements):
        return {"recorded": False, "error": "not_licensed"}

    response_type = meta["response_type"]
    answer: Dict[str, Any] = {"response_type": response_type}

    if response_type == "drawing":
        if not payload.get("drawing_data") and not payload.get("meta", {}).get("has_strokes"):
            return {"recorded": False, "error": "empty_drawing"}
        answer["drawing_data"] = payload.get("drawing_data")
        answer["meta"] = payload.get("meta") or {}
        answer["association"] = (payload.get("association") or payload.get("text") or "").strip()
    elif response_type == "inkblot":
        text = (payload.get("association") or payload.get("text") or "").strip()
        if not text:
            return {"recorded": False, "error": "empty_association"}
        answer["association"] = text
    elif response_type == "tat_story":
        story = payload.get("story") or {}
        if not any(str(story.get(k) or "").strip() for k in ("happening", "feeling", "outcome")):
            return {"recorded": False, "error": "empty_story"}
        answer["story"] = story
    else:
        text = (payload.get("text") or "").strip()
        if not text:
            return {"recorded": False, "error": "empty_text"}
        answer["text"] = text

    answer["item_score"] = score_item_response(item_id, response_type, answer)
    store["answers"].setdefault(instrument, {})[item_id] = answer
    session.assessments_completed += 1

    try:
        from app.services.maum_organism import emit_activity

        emit_activity(
            session.user_id,
            "projective_answer",
            {"instrument": instrument, "item_id": item_id, "response_type": response_type},
            source_id=f"projective:{session.session_id}:{item_id}",
        )
    except Exception:
        pass

    return {"recorded": True, "item_score": answer["item_score"]}


def picture_assessment_results(session) -> Dict[str, Any]:
    store = _store(session)
    answers = store.get("answers") or {}
    catalog = projective_battery_catalog()
    progress: Dict[str, Any] = {}
    answered = 0
    for inst in catalog["instruments"]:
        iid = inst["instrument_id"]
        total = inst["item_count"]
        done = len(answers.get(iid, {}))
        answered += done
        progress[iid] = {
            "answered": done,
            "total": total,
            "completion_rate": round(done / total, 2) if total else 0.0,
        }

    scores = score_projective_battery(answers, _item_lookup())
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "mode": "clinical_projective",
        "instrument_count": catalog["instrument_count"],
        "total_items": catalog["total_items"],
        "answered_items": answered,
        "skipped_items": len(store.get("skipped") or []),
        "progress": progress,
        "projective_scores": scores,
        "disclaimer": catalog.get("disclaimer"),
    }
