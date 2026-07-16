"""Commercial license types for B2C / B2B society subscription model (patent/B2B)."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional


class LicenseType(str, Enum):
    B2C_PERSONAL = "B2C_personal"
    B2B_SOCIETY_GENERAL = "B2B_society_general"  # 상담학회 · 월 99만
    B2B_SOCIETY_CLINICAL = "B2B_society_clinical"  # 임상학회 · 월 150만
    B2B_SOCIETY_MEDICAL = "B2B_society_medical"  # 정신학회 · 월 250만
    B2B_SOCIETY_FAITH = "B2B_society_faith"  # 기독교학회 · 월 129만


LICENSE_TYPE_CATALOG: Dict[str, Dict[str, Any]] = {
    LicenseType.B2C_PERSONAL.value: {
        "licenseType": LicenseType.B2C_PERSONAL.value,
        "label_ko": "개인 (B2C)",
        "price_krw_monthly": 0,
        "price_label": "개인 구독",
        "b2b": False,
        "sos_enabled": False,
        "pii_mask_required": False,
        "default_consultation_mode": "psychology",
    },
    LicenseType.B2B_SOCIETY_GENERAL.value: {
        "licenseType": LicenseType.B2B_SOCIETY_GENERAL.value,
        "label_ko": "상담학회 (단체)",
        "price_krw_monthly": 990_000,
        "price_label": "월 99만원",
        "b2b": True,
        "sos_enabled": True,
        "pii_mask_required": True,
        "default_consultation_mode": "psychology",
        "discipline_ids": ["counseling_society", "integrative_society"],
    },
    LicenseType.B2B_SOCIETY_CLINICAL.value: {
        "licenseType": LicenseType.B2B_SOCIETY_CLINICAL.value,
        "label_ko": "임상·심리학회 (단체)",
        "price_krw_monthly": 1_500_000,
        "price_label": "월 150만원",
        "b2b": True,
        "sos_enabled": True,
        "pii_mask_required": True,
        "default_consultation_mode": "psychology",
        "discipline_ids": ["clinical_psych_trainee", "psychology_society", "mh_social_work_trainee"],
    },
    LicenseType.B2B_SOCIETY_MEDICAL.value: {
        "licenseType": LicenseType.B2B_SOCIETY_MEDICAL.value,
        "label_ko": "정신의학회 (단체)",
        "price_krw_monthly": 2_500_000,
        "price_label": "월 250만원",
        "b2b": True,
        "sos_enabled": True,
        "pii_mask_required": True,
        "default_consultation_mode": "psychology",
        "discipline_ids": ["psychiatry_society"],
    },
    LicenseType.B2B_SOCIETY_FAITH.value: {
        "licenseType": LicenseType.B2B_SOCIETY_FAITH.value,
        "label_ko": "기독교·목회상담 학회 (단체)",
        "price_krw_monthly": 1_290_000,
        "price_label": "월 129만원",
        "b2b": True,
        "sos_enabled": True,
        "pii_mask_required": True,
        "default_consultation_mode": "faith",
        "discipline_ids": ["faith_counseling_society"],
    },
}


def normalize_license_type(raw: Any) -> str:
    text = str(raw or "").strip()
    if text in LICENSE_TYPE_CATALOG:
        return text
    lowered = text.lower().replace("-", "_")
    aliases = {
        "b2c": LicenseType.B2C_PERSONAL.value,
        "personal": LicenseType.B2C_PERSONAL.value,
        "b2c_personal": LicenseType.B2C_PERSONAL.value,
        "general": LicenseType.B2B_SOCIETY_GENERAL.value,
        "counseling": LicenseType.B2B_SOCIETY_GENERAL.value,
        "clinical": LicenseType.B2B_SOCIETY_CLINICAL.value,
        "medical": LicenseType.B2B_SOCIETY_MEDICAL.value,
        "psychiatry": LicenseType.B2B_SOCIETY_MEDICAL.value,
        "faith": LicenseType.B2B_SOCIETY_FAITH.value,
        "christian": LicenseType.B2B_SOCIETY_FAITH.value,
    }
    return aliases.get(lowered, LicenseType.B2C_PERSONAL.value)


def is_b2b_license(license_type: Any) -> bool:
    meta = LICENSE_TYPE_CATALOG.get(normalize_license_type(license_type)) or {}
    return bool(meta.get("b2b"))


def license_type_from_discipline(discipline_id: Optional[str]) -> str:
    did = (discipline_id or "").strip()
    for lic, meta in LICENSE_TYPE_CATALOG.items():
        if did and did in (meta.get("discipline_ids") or []):
            return lic
    return LicenseType.B2C_PERSONAL.value


def catalog_for_api() -> Dict[str, Any]:
    return {
        "license_types": list(LICENSE_TYPE_CATALOG.values()),
        "consultation_modes": ["psychology", "faith"],
        "non_diagnostic": True,
    }
