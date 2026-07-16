"""Resolve commercial licenseType + organizationId on users/sessions."""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.models.commercial_license import (
    LICENSE_TYPE_CATALOG,
    LicenseType,
    catalog_for_api,
    is_b2b_license,
    license_type_from_discipline,
    normalize_license_type,
)
from app.services.persistence import get_user_settings, save_user_settings

SETTINGS_LICENSE = "licenseType"
SETTINGS_ORG = "organizationId"


def resolve_license_context(
    user_id: str,
    *,
    session: Any = None,
    override_license_type: Optional[str] = None,
    override_org_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Priority: override → session fields/entitlements → user settings → B2C."""
    settings = get_user_settings(user_id)

    license_type = None
    org_id = None

    if override_license_type:
        license_type = normalize_license_type(override_license_type)
    if override_org_id:
        org_id = override_org_id

    if session is not None:
        if not license_type:
            license_type = getattr(session, "license_type", None) or None
        if not org_id:
            org_id = getattr(session, "organization_id", None) or getattr(session, "org_id", None)
        ents = getattr(session, "org_entitlements", None) or {}
        if not license_type:
            license_type = ents.get("licenseType") or license_type_from_discipline(ents.get("discipline_id"))
        if not org_id:
            org_id = ents.get("org_id") or getattr(session, "org_id", None)

    if not license_type:
        license_type = settings.get(SETTINGS_LICENSE) or settings.get("license_type")
    if not org_id:
        org_id = settings.get(SETTINGS_ORG) or settings.get("organization_id")

    license_type = normalize_license_type(license_type)
    meta = LICENSE_TYPE_CATALOG.get(license_type) or LICENSE_TYPE_CATALOG[LicenseType.B2C_PERSONAL.value]

    if session is not None:
        session.license_type = license_type
        session.organization_id = org_id
        if org_id and not getattr(session, "org_id", None):
            session.org_id = org_id

    return {
        "user_id": user_id,
        "licenseType": license_type,
        "organizationId": org_id,
        "b2b": bool(meta.get("b2b")),
        "sos_enabled": bool(meta.get("sos_enabled")),
        "pii_mask_required": bool(meta.get("pii_mask_required")),
        "meta": meta,
        "catalog": catalog_for_api(),
    }


def save_license_context(
    user_id: str,
    *,
    license_type: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> Dict[str, Any]:
    settings = get_user_settings(user_id)
    if license_type is not None:
        lt = normalize_license_type(license_type)
        settings[SETTINGS_LICENSE] = lt
        settings["license_type"] = lt
    if organization_id is not None:
        settings[SETTINGS_ORG] = organization_id or None
        settings["organization_id"] = organization_id or None
    save_user_settings(user_id, settings)
    return resolve_license_context(user_id)


def apply_entitlements_license_type(entitlements: Dict[str, Any]) -> Dict[str, Any]:
    """Stamp licenseType onto association entitlements dict."""
    ents = dict(entitlements or {})
    if not ents.get("licenseType"):
        ents["licenseType"] = license_type_from_discipline(ents.get("discipline_id"))
    ents["b2b"] = is_b2b_license(ents["licenseType"])
    return ents
