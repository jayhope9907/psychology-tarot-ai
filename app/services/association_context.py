"""학회 라이선스를 세션·플랜에 바인딩."""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.chat_session import ChatSessionState
from app.services.license_store import assign_member, validate_license

LICENSE_REASON_KO = {
    "empty_key": "라이선스 키가 비어 있어요",
    "not_found": "등록되지 않은 키예요",
    "inactive": "비활성화된 라이선스예요",
    "expired": "만료된 라이선스예요",
}


def resolve_api_license(
    license_key: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """API용 라이선스 해석 — 키가 있으면 유효성도 함께 반환."""
    ctx: Dict[str, Any] = {
        "entitlements": None,
        "license_key": None,
        "license_valid": None,
        "license_reason": None,
        "license_reason_ko": None,
        "org_name": None,
    }
    if license_key:
        key = license_key.strip().upper()
        ctx["license_key"] = key
        lic = validate_license(key)
        ctx["license_valid"] = bool(lic.get("valid"))
        if lic.get("valid"):
            ctx["entitlements"] = {**(lic.get("entitlements") or {}), "org_name": lic.get("org_name")}
            ctx["org_name"] = lic.get("org_name")
        else:
            reason = lic.get("reason") or "invalid"
            ctx["license_reason"] = reason
            ctx["license_reason_ko"] = LICENSE_REASON_KO.get(reason, "유효하지 않은 라이선스예요")
        return ctx

    if user_id:
        from app.services.persistence import load_latest_session_for_user

        session = load_latest_session_for_user(user_id)
        if session and session.org_entitlements:
            ctx["entitlements"] = {**session.org_entitlements, "org_name": session.org_name}
            ctx["org_name"] = session.org_name
    return ctx


def ensure_session_entitlements(session: ChatSessionState) -> None:
    """저장된 세션에 entitlements가 없으면 라이선스 키로 재바인딩."""
    if session.org_entitlements:
        return
    if session.association_license_key:
        bind_license_to_session(session, session.association_license_key, assign_user=False)


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
        return {
            "bound": False,
            "reason": result.get("reason"),
            "reason_ko": LICENSE_REASON_KO.get(result.get("reason", ""), "유효하지 않은 라이선스예요"),
            "valid": False,
        }

    entitlements = result.get("entitlements") or {}
    session.association_license_key = result["license_key"]
    session.org_id = result["org_id"]
    session.org_name = result["org_name"]
    session.org_entitlements = entitlements

    plan = entitlements.get("plan_override")
    if plan:
        session.plan = plan

    from app.services.association_agent import (
        agent_from_license_metadata,
        apply_agent_to_session,
        build_association_agent,
    )

    metadata = result.get("metadata") or {}
    agent = agent_from_license_metadata(metadata) or build_association_agent(
        entitlements, org_name=session.org_name or ""
    )
    apply_agent_to_session(session, agent)

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
        "agent_profile": agent,
        "demo_cases": result.get("demo_cases") or metadata.get("demo_cases") or [],
    }
