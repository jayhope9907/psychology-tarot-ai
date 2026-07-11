from app.services.association_licensing import filter_catalog_by_entitlements, resolve_entitlements
from app.services.clinical_catalog import unified_clinical_catalog
from app.models.association import AssociationDiscipline, LicenseTier


def test_psychology_license_includes_projective():
    ent = resolve_entitlements(AssociationDiscipline.PSYCHOLOGY.value, LicenseTier.SOCIETY.value)
    assert "clinical_hub" in ent["feature_flags"]
    assert ent["feature_flags"]["projective_battery"] is True
    assert "rorschach" in ent["allowed_projective"]
    assert "dap" in ent["allowed_projective"]


def test_psychiatry_license_limits_projective():
    ent = resolve_entitlements(AssociationDiscipline.PSYCHIATRY.value, LicenseTier.FEDERATION.value)
    assert ent["feature_flags"]["projective_battery"] is False
    catalog = unified_clinical_catalog(ent)
    assert catalog["projective_instruments"] == []


def test_counseling_license_has_drawing_not_inkblot():
    ent = resolve_entitlements(AssociationDiscipline.COUNSELING.value, LicenseTier.SOCIETY.value)
    assert "htp" in ent["allowed_projective"]
    assert "rorschach" not in ent["allowed_projective"]
    catalog = unified_clinical_catalog(ent)
    proj_ids = {p["instrument_id"] for p in catalog["projective_instruments"]}
    assert "htp" in proj_ids
    assert "rorschach" not in proj_ids


def test_catalog_user_friendly_title():
    catalog = unified_clinical_catalog()
    assert catalog["user_title"] == "나를 알아가는 시간"
    assert "검사" not in catalog["user_title"]
