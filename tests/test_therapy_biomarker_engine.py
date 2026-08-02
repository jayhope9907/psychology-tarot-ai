"""Full ClinicalSchool therapy biomarker engine tests."""

from app.models.clinical import ClinicalSchool
from app.services.therapy_biomarker_engine import (
    AXIS_SPECS,
    TherapyEngineCalculator,
    assert_axes_cover_clinical_schools,
    get_therapy_catalog,
)


def test_axes_cover_every_clinical_school():
    assert assert_axes_cover_clinical_schools() == []
    assert len(AXIS_SPECS) == len(ClinicalSchool)


def test_therapy_catalog_includes_modern_waves():
    catalog = get_therapy_catalog()
    assert catalog["count"] == len(ClinicalSchool)
    assert catalog["non_diagnostic"] is True
    assert "modern_cbt" in catalog["waves"]
    assert "brief_trauma" in catalog["waves"]
    ids = {a["id"] for a in catalog["axes"]}
    assert "ifsSelfLeadershipScore" in ids
    assert "dbtRegulationScore" in ids
    assert "actValuesScore" in ids
    assert "baActivationScore" in ids
    assert "polyvagalSafetyScore" in ids


def test_extract_therapy_vector_matches_ts_coefficients():
    calc = TherapyEngineCalculator()
    raw = {
        "psychoanalysisInsightMs": 400,
        "adlerResilienceDelayMs": 250,
        "logotherapyEnduranceSec": 12,
        "personCenteredStability": 1.5,
        "existentialAutonomyRatio": 0.82,
        "realityFocusRatio": 0.7,
        "cbtCognitiveShiftMs": 500,
        "solutionOrientedRatio": 0.88,
        "positiveStrengthBoost": 7.5,
        "dbtDistressToleranceRatio": 0.9,
        "actValuesCommittedActionRatio": 0.85,
        "ifsSelfLeadershipRatio": 0.77,
        "baActivityCompletionRatio": 0.66,
    }
    vec = calc.extract_therapy_vector("user-a", raw)
    assert vec["userId"] == "user-a"
    assert vec["insightScore"] == 80.0
    assert vec["courageScore"] == 80.0
    assert vec["meaningScore"] == 60.0
    assert vec["acceptanceScore"] == 85.0
    assert vec["autonomyScore"] == 82.0
    assert vec["realityScore"] == 70.0
    assert vec["cbtShiftScore"] == 80.0
    assert vec["solutionScore"] == 88
    assert vec["strengthsScore"] == 75.0
    assert vec["dbtRegulationScore"] == 90.0
    assert vec["actValuesScore"] == 85.0
    assert vec["ifsSelfLeadershipScore"] == 77.0
    assert vec["baActivationScore"] == 66.0
    assert vec["axisCount"] == len(ClinicalSchool)
    assert vec["bySchool"]["DBT"] == 90.0
    assert vec["non_diagnostic"] is True


def test_extract_clamps_and_defaults():
    calc = TherapyEngineCalculator()
    vec = calc.extract_therapy_vector("u", {"psychoanalysisInsightMs": 999999})
    assert vec["insightScore"] == 0.0
    assert 0.0 <= vec["courageScore"] <= 100.0


def test_therapeutic_synergy_includes_modern_layer():
    calc = TherapyEngineCalculator()
    a = {
        "cbtShiftScore": 80,
        "solutionScore": 88,
        "courageScore": 70,
        "dbtRegulationScore": 90,
        "actValuesScore": 80,
        "traumaSafetyScore": 70,
        "bySchool": {"SOLUTION_FOCUSED": 88, "DBT": 90, "ACT": 80},
    }
    b = {
        "cbtShiftScore": 70,
        "solutionScore": 60,
        "courageScore": 40,
        "dbtRegulationScore": 80,
        "actValuesScore": 70,
        "traumaSafetyScore": 60,
        "bySchool": {"BECK_CBT": 70, "DBT": 80},
    }
    # classic = 90*0.4 + 74*0.3 + 100*0.3 = 88.2
    # modern = 90*0.34 + 75*0.33 + 65*0.33 = 30.6 + 24.75 + 21.45 = 76.8
    # final = round(88.2*0.7 + 76.8*0.3) = round(61.74+23.04)=85
    result = calc.calculate_therapeutic_synergy(a, b)
    assert result["finalTherapyMatchScore"] == 85
    assert result["primaryTherapeuticType"] == "해결중심적 스페셜리스트"
    assert "modernHarmony" in result["components"]
    assert result["non_diagnostic"] is True


def test_new_clinical_schools_in_theory_catalog():
    from app.services.counseling_theories import THEORY_CATALOG

    assert set(THEORY_CATALOG.keys()) == set(ClinicalSchool)
    for school in (
        ClinicalSchool.IFS,
        ClinicalSchool.BEHAVIORAL_ACTIVATION,
        ClinicalSchool.CPT_INFORMED,
        ClinicalSchool.SOMATIC_EXPERIENCING,
        ClinicalSchool.POLYVAGAL_INFORMED,
        ClinicalSchool.PROLONGED_EXPOSURE_INFORMED,
    ):
        assert school in THEORY_CATALOG
        assert THEORY_CATALOG[school]["techniques"]


def test_therapy_biomarker_api_endpoints():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    catalog = client.get("/api/v1/therapy-biomarkers/catalog")
    assert catalog.status_code == 200
    assert catalog.json()["count"] == len(ClinicalSchool)

    extract = client.post(
        "/api/v1/therapy-biomarkers/extract",
        json={
            "user_id": "api-user",
            "raw": {
                "psychoanalysisInsightMs": 400,
                "solutionOrientedRatio": 0.88,
                "dbtDistressToleranceRatio": 0.91,
                "ifsSelfLeadershipRatio": 0.8,
            },
        },
    )
    assert extract.status_code == 200
    vec = extract.json()["vector"]
    assert vec["insightScore"] == 80.0
    assert vec["solutionScore"] == 88
    assert vec["dbtRegulationScore"] == 91.0
    assert vec["ifsSelfLeadershipScore"] == 80.0

    synergy = client.post(
        "/api/v1/therapy-biomarkers/synergy",
        json={
            "user_a": {
                "userId": "api-user",
                "cbtShiftScore": 80,
                "solutionScore": 88,
                "courageScore": 70,
                "dbtRegulationScore": 50,
                "actValuesScore": 50,
                "traumaSafetyScore": 50,
            },
            "user_b": {
                "userId": "partner",
                "cbtShiftScore": 70,
                "solutionScore": 60,
                "courageScore": 40,
                "dbtRegulationScore": 50,
                "actValuesScore": 50,
                "traumaSafetyScore": 50,
            },
        },
    )
    assert synergy.status_code == 200
    body = synergy.json()
    assert body["non_diagnostic"] is True
    assert 0 <= body["finalTherapyMatchScore"] <= 100
