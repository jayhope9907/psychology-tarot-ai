"""학회 라이선스를 세션·플랜에 바인딩."""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.chat_session import ChatSessionState
from app.services.license_store import assign_member, validate_license


def bind_license_to_session(
    session: ChatSessionState,
    license_key: Optional[str],
    *,
    assign_user: bool = True,
) -> Dict[str, Any]:
    key = (license_key or session.association_license_key or "").strip()
    if not key:
        return {"bound": False}

    result = validate_license(key)
    if not result.get("valid"):
        return {"bound": False, "reason": result.get("reason"), "valid": False}

    entitlements = result.get("entitlements") or {}
    session.association_license_key = result["license_key"]
    session.org_id = result["org_id"]
    session.org_name = result["org_name"]
    session.org_entitlements = entitlements

    plan = entitlements.get("plan_override")
    if plan:
        session.plan = plan

    if assign_user and session.user_id:
        assign_member(result["org_id"], session.user_id)

    return {
        "bound": True,
        "valid": True,
        "org_id": session.org_id,
        "org_name": session.org_name,
        "discipline_id": entitlements.get("discipline_id"),
        "discipline_label": entitlements.get("discipline_label"),
        "tier_label": entitlements.get("tier_label"),
        "entitlements": entitlements,
    }
