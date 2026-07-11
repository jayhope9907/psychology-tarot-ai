"""학회 라이선스 저장·검증."""
from __future__ import annotations

import json
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.db.database import get_connection, init_db
from app.models.association import AssociationDiscipline, LicenseTier
from app.services.association_licensing import resolve_entitlements

DEMO_LICENSES: Dict[str, Dict[str, Any]] = {
    "MSHT-COUNSEL-DEMO-2026": {
        "org_name": "데모 · 한국상담학회 연수원",
        "discipline_id": AssociationDiscipline.COUNSELING.value,
        "tier_id": LicenseTier.SOCIETY.value,
    },
    "MSHT-PSYCH-DEMO-2026": {
        "org_name": "데모 · 한국심리학회 교육위",
        "discipline_id": AssociationDiscipline.PSYCHOLOGY.value,
        "tier_id": LicenseTier.SOCIETY.value,
    },
    "MSHT-PSYCHIATRY-DEMO-2026": {
        "org_name": "데모 · 정신의학회 CME",
        "discipline_id": AssociationDiscipline.PSYCHIATRY.value,
        "tier_id": LicenseTier.FEDERATION.value,
        "secondary_discipline": AssociationDiscipline.PSYCHOLOGY.value,
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_tables() -> None:
    init_db()


def _seed_demo_licenses(conn) -> None:
    today = date.today()
    valid_until = (today + timedelta(days=365)).isoformat()
    valid_from = today.isoformat()
    for key, meta in DEMO_LICENSES.items():
        existing = conn.execute(
            "SELECT license_key FROM organization_licenses WHERE license_key = ?",
            (key,),
        ).fetchone()
        if existing:
            continue
        org_id = f"org-{meta['discipline_id'][:6]}-demo"
        conn.execute(
            """
            INSERT OR IGNORE INTO organizations
                (org_id, org_name, discipline_id, tier_id, secondary_discipline_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                org_id,
                meta["org_name"],
                meta["discipline_id"],
                meta["tier_id"],
                meta.get("secondary_discipline"),
                _utc_now(),
            ),
        )
        from app.services.association_licensing import LICENSE_TIERS

        seats = LICENSE_TIERS.get(meta["tier_id"], {}).get("seats", 150)
        conn.execute(
            """
            INSERT INTO organization_licenses
                (license_key, org_id, valid_from, valid_until, seats_total, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                key,
                org_id,
                valid_from,
                valid_until,
                seats,
                json.dumps({"demo": True}, ensure_ascii=False),
            ),
        )


def validate_license(license_key: str) -> Dict[str, Any]:
    _ensure_tables()
    key = (license_key or "").strip().upper()
    if not key:
        return {"valid": False, "reason": "empty_key"}

    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT l.license_key, l.org_id, l.valid_from, l.valid_until, l.seats_total,
                   l.seats_used, l.status, o.org_name, o.discipline_id, o.tier_id,
                   o.secondary_discipline_id, o.branding_json
            FROM organization_licenses l
            JOIN organizations o ON o.org_id = l.org_id
            WHERE l.license_key = ?
            """,
            (key,),
        ).fetchone()
        if not row:
            return {"valid": False, "reason": "not_found"}

        if row["status"] != "active":
            return {"valid": False, "reason": "inactive"}

        until = date.fromisoformat(str(row["valid_until"])[:10])
        if until < date.today():
            return {"valid": False, "reason": "expired", "valid_until": row["valid_until"]}

        entitlements = resolve_entitlements(
            row["discipline_id"],
            row["tier_id"],
            secondary_discipline=row["secondary_discipline_id"],
        )
        branding = json.loads(row["branding_json"] or "{}")
        return {
            "valid": True,
            "license_key": row["license_key"],
            "org_id": row["org_id"],
            "org_name": row["org_name"],
            "valid_until": row["valid_until"],
            "seats_total": row["seats_total"],
            "seats_used": row["seats_used"],
            "entitlements": entitlements,
            "branding": branding,
        }
    finally:
        conn.close()


def provision_license(
    org_name: str,
    discipline_id: str,
    tier_id: str,
    *,
    secondary_discipline: Optional[str] = None,
    seats: Optional[int] = None,
    days_valid: int = 365,
) -> Dict[str, Any]:
    _ensure_tables()
    from app.services.association_licensing import LICENSE_TIERS

    org_id = f"org-{secrets.token_hex(6)}"
    license_key = f"MSHT-{discipline_id[:4].upper()}-{secrets.token_hex(4).upper()}"
    tier = LICENSE_TIERS.get(tier_id, LICENSE_TIERS[LicenseTier.SOCIETY.value])
    seat_count = seats or tier.get("seats", 150)
    today = date.today()
    valid_until = (today + timedelta(days=days_valid)).isoformat()

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO organizations
                (org_id, org_name, discipline_id, tier_id, secondary_discipline_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (org_id, org_name, discipline_id, tier_id, secondary_discipline, _utc_now()),
        )
        conn.execute(
            """
            INSERT INTO organization_licenses
                (license_key, org_id, valid_from, valid_until, seats_total)
            VALUES (?, ?, ?, ?, ?)
            """,
            (license_key, org_id, today.isoformat(), valid_until, seat_count),
        )
        conn.commit()
    finally:
        conn.close()

    result = validate_license(license_key)
    result["provisioned"] = True
    return result


def assign_member(org_id: str, user_id: str, role: str = "member") -> Dict[str, Any]:
    _ensure_tables()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO organization_members (org_id, user_id, role)
            VALUES (?, ?, ?)
            ON CONFLICT(org_id, user_id) DO UPDATE SET role = excluded.role
            """,
            (org_id, user_id, role),
        )
        conn.execute(
            """
            UPDATE organization_licenses SET seats_used = (
                SELECT COUNT(*) FROM organization_members WHERE org_id = ?
            ) WHERE org_id = ?
            """,
            (org_id, org_id),
        )
        conn.commit()
        return {"org_id": org_id, "user_id": user_id, "role": role}
    finally:
        conn.close()


def list_organizations(limit: int = 20) -> List[Dict[str, Any]]:
    _ensure_tables()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT o.org_id, o.org_name, o.discipline_id, o.tier_id,
                   l.license_key, l.seats_total, l.seats_used, l.valid_until, l.status
            FROM organizations o
            LEFT JOIN organization_licenses l ON l.org_id = o.org_id
            ORDER BY o.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
