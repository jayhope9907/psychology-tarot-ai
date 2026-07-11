"""Association licensing tests."""
from __future__ import annotations

from app.db.database import reset_db
from app.models.association import AssociationDiscipline, LicenseTier
from app.services.association_context import bind_license_to_session
from app.services.association_licensing import (
    build_associations_catalog,
    instrument_allowed,
    resolve_entitlements,
)
from app.services.assessment_selector import _available_candidates
from app.services.chat_session import ChatSessionState
from app.services.license_store import validate_license


def test_catalog_has_three_disciplines_and_tiers():
    catalog = build_associations_catalog()
    ids = {d["discipline_id"] for d in catalog["disciplines"]}
    assert AssociationDiscipline.COUNSELING.value in ids
    assert AssociationDiscipline.PSYCHOLOGY.value in ids
    assert AssociationDiscipline.PSYCHIATRY.value in ids
    assert len(catalog["license_tiers"]) >= 4
    assert catalog["comparison_matrix"]


def test_counseling_vs_psychiatry_instruments_differ():
    c = resolve_entitlements(AssociationDiscipline.COUNSELING.value, LicenseTier.SOCIETY.value)
    p = resolve_entitlements(AssociationDiscipline.PSYCHIATRY.value, LicenseTier.SOCIETY.value)
    assert "sct" in c["allowed_instruments"]
    assert "pcl5" in p["allowed_instruments"]
    assert "tarot_reflect" in c["allowed_instruments"]
    assert "tarot_reflect" not in p["allowed_instruments"]


def test_demo_counseling_license_validates():
    reset_db()
    result = validate_license("MSHT-COUNSEL-DEMO-2026")
    assert result["valid"] is True
    assert "상담" in result["org_name"] or "데모" in result["org_name"]
    assert result["entitlements"]["discipline_id"] == AssociationDiscipline.COUNSELING.value


def test_bind_license_filters_assessment_candidates():
    reset_db()
    session = ChatSessionState(user_id="u-lic", session_id="s-lic")
    bind_license_to_session(session, "MSHT-PSYCHIATRY-DEMO-2026")
    candidates = _available_candidates(session)
    assert "pcl5" in candidates
    assert "tarot_reflect" not in candidates

    session2 = ChatSessionState(user_id="u-lic2", session_id="s-lic2")
    bind_license_to_session(session2, "MSHT-COUNSEL-DEMO-2026")
    c2 = _available_candidates(session2)
    assert "sct" in c2
    assert "pcl5" not in c2
