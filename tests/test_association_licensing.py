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
    assert AssociationDiscipline.CLINICAL_PSYCH_TRAINEE.value in ids
    assert AssociationDiscipline.MH_SOCIAL_WORK.value in ids
    assert len(catalog["license_tiers"]) >= 4
    assert catalog["comparison_matrix"]


def test_trainee_licenses_entitlements():
    clinical = resolve_entitlements(
        AssociationDiscipline.CLINICAL_PSYCH_TRAINEE.value, LicenseTier.SOCIETY.value
    )
    mhsw = resolve_entitlements(
        AssociationDiscipline.MH_SOCIAL_WORK.value, LicenseTier.SOCIETY.value
    )
    assert "rorschach" in clinical["allowed_projective"]
    assert "tat" in clinical["allowed_projective"]
    assert clinical["feature_flags"]["dsm5_catalog"] is True
    assert clinical["feature_flags"]["tarot_bridge"] is False
    assert clinical["feature_flags"]["emotional_spectrum"] is True
    assert clinical["feature_flags"]["mind_network_3d"] is True
    assert clinical["feature_flags"]["age_cohort_export"] is True
    assert clinical["feature_flags"]["integrated_diagnostic"] is True
    assert "pcl5" in mhsw["allowed_instruments"]
    assert "rorschach" not in mhsw["allowed_projective"]
    assert mhsw["feature_flags"]["tarot_bridge"] is False


def test_chapter_tier_disables_age_cohort_export():
    chapter = resolve_entitlements(
        AssociationDiscipline.PSYCHOLOGY.value, LicenseTier.CHAPTER.value
    )
    society = resolve_entitlements(
        AssociationDiscipline.PSYCHOLOGY.value, LicenseTier.SOCIETY.value
    )
    assert chapter["feature_flags"]["age_cohort_export"] is False
    assert chapter["feature_flags"]["b2b_export"] is False
    assert society["feature_flags"]["age_cohort_export"] is True
    assert society["feature_flags"]["mind_network_3d"] is True


def test_demo_trainee_licenses_validate():
    reset_db()
    clinical = validate_license("MSHT-CLINICAL-DEMO-2026")
    assert clinical["valid"] is True
    assert clinical["entitlements"]["discipline_id"] == AssociationDiscipline.CLINICAL_PSYCH_TRAINEE.value
    assert "임상심리" in clinical["entitlements"]["discipline_label"]

    mhsw = validate_license("MSHT-MHSW-DEMO-2026")
    assert mhsw["valid"] is True
    assert mhsw["entitlements"]["discipline_id"] == AssociationDiscipline.MH_SOCIAL_WORK.value
    assert "정신보건" in mhsw["entitlements"]["discipline_label"]


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
