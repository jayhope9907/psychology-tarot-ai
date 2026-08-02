"""Evidence corpus + PBT/FIT architecture tests."""

from app.services.process_based_therapy import (
    build_fit_feedback,
    build_paper_architecture_bundle,
    extract_process_dimensions,
    trauma_safety_gate,
)
from app.services.therapy_biomarker_engine import get_therapy_catalog
from app.services.therapy_evidence_corpus import (
    EVIDENCE_PAPERS,
    build_evidence_corpus,
    list_evidence_papers,
)


def test_evidence_corpus_has_doi_and_hooks():
    corpus = build_evidence_corpus()
    assert corpus["paper_count"] >= 20
    assert corpus["non_diagnostic"] is True
    assert "process_based_therapy" in corpus["by_architecture_hook"]
    for paper in EVIDENCE_PAPERS:
        assert paper["doi"]
        assert paper["schools"]
        assert paper["architecture_hooks"]


def test_list_evidence_filters():
    act = list_evidence_papers(school="ACT")
    assert any(p["id"] == "hayes_hofmann_2017_pbt" for p in act)
    pbt = list_evidence_papers(hook="process_based_therapy")
    assert len(pbt) >= 2
    recent = list_evidence_papers(year_from=2017)
    assert all(p["year"] >= 2017 for p in recent)


def test_catalog_attaches_evidence_papers():
    catalog = get_therapy_catalog()
    assert catalog["evidence_paper_count"] == len(EVIDENCE_PAPERS)
    assert "process_based_therapy" in catalog["architecture_hooks"]
    dbt_axes = [a for a in catalog["axes"] if a["school"] == "DBT"]
    assert dbt_axes
    assert dbt_axes[0]["evidence_count"] >= 1
    assert dbt_axes[0]["evidence_papers"][0]["doi"]


def test_process_dimensions_and_safety_gate():
    vector = {
        "actValuesScore": 80,
        "acceptanceScore": 75,
        "cftCompassionScore": 70,
        "mbctDecenteringScore": 65,
        "mindfulnessScore": 60,
        "gestaltPresenceScore": 55,
        "insightScore": 50,
        "solutionScore": 40,
        "baActivationScore": 35,
        "realityScore": 45,
        "miChangeTalkScore": 30,
        "courageScore": 40,
        "dbtRegulationScore": 80,
        "traumaSafetyScore": 85,
        "polyvagalSafetyScore": 80,
        "seTitrationScore": 75,
        "eftBondScore": 50,
        "attachmentSecureScore": 55,
        "iptRoleScore": 50,
        "ifsSelfLeadershipScore": 60,
    }
    dims = extract_process_dimensions(vector)
    assert dims["primaryBottleneck"] in {
        "openness",
        "awareness",
        "engagement",
        "regulation",
        "relatedness",
    }
    assert 0 <= dims["psychologicalFlexibilityProxy"] <= 100
    assert dims["non_diagnostic"] is True

    gate = trauma_safety_gate(vector)
    assert gate["level"] == "engage"
    assert gate["allowIntenseExploration"] is True

    low = trauma_safety_gate({"traumaSafetyScore": 20, "polyvagalSafetyScore": 20})
    assert low["level"] == "stabilize"
    assert low["allowIntenseExploration"] is False


def test_fit_and_architecture_bundle():
    vector = {"actValuesScore": 70, "solutionScore": 30, "baActivationScore": 25}
    fit = build_fit_feedback(progress_score=28, alliance_score=35, process_dims={"psychologicalFlexibilityProxy": 40})
    assert "low_progress" in fit["riskFlags"]
    assert fit["stance"] == "repair"

    bundle = build_paper_architecture_bundle(
        vector, progress_score=80, alliance_score=75
    )
    assert "process_based_therapy" in bundle
    assert "fit_session_feedback" in bundle
    assert "trauma_safety_gate" in bundle
    assert len(bundle["architecture_modules"]) >= 4
    assert any(m["id"] == "therapy_evidence_corpus" for m in bundle["architecture_modules"])
