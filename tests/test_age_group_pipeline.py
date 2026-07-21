"""AgeGroupDataPipeline — cohort bucketing, anonymization, hospital export."""
from __future__ import annotations

import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    db = tmp_path / "age_cohort.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.delenv("RESEARCH_EXPORT_TOKEN", raising=False)
    monkeypatch.delenv("PURGE_AUDIT_TOKEN", raising=False)
    from app.db import database as dbmod

    dbmod._initialized = False
    dbmod._db_path = str(db)
    dbmod.init_db(force=True)
    yield str(db)
    dbmod._initialized = False


def test_resolve_age_group_ranges():
    from app.services.dsm5_integrator import resolve_age_group

    assert resolve_age_group(age_years=0) == "pediatric"
    assert resolve_age_group(age_years=12) == "pediatric"
    assert resolve_age_group(age_years=13) == "adolescent"
    assert resolve_age_group(age_years=17) == "adolescent"
    assert resolve_age_group(age_years=18) == "young_adult"
    assert resolve_age_group(age_years=29) == "young_adult"
    assert resolve_age_group(age_years=30) == "middle_adult"
    assert resolve_age_group(age_years=59) == "middle_adult"
    assert resolve_age_group(age_years=60) == "older_adult"
    assert resolve_age_group(age_years=95) == "older_adult"
    assert resolve_age_group(age_group="청년") == "young_adult"
    assert resolve_age_group(age_group="young-adult") == "young_adult"
    assert resolve_age_group(age_group="nope") is None


def test_integrated_metrics_canonical_keys(isolated_db):
    from app.services.emotional_spectrum import compute_emotional_spectrum
    from app.services.dsm5_integrator import build_integrated_metrics, COGNITIVE_AXES

    result = compute_emotional_spectrum(
        base_scores={"depressive": 70, "anxiety": 60, "somatic": 40},
        behavioral_metrics={"hesitation_index": 0.5, "backspace_count": 8},
    )
    metrics = build_integrated_metrics(result, session_id="s1", patient_id="should-not-leak")
    assert set(metrics["cognitiveProfile"].keys()) == set(COGNITIVE_AXES)
    assert set(metrics["clinicalProfile"].keys()) == {
        "schizophrenia_index",
        "asd_stimming_index",
        "depression_index",
    }
    assert set(metrics["threeRenderMetrics"].keys()) == {
        "backbone_tension",
        "cluster_density",
    }
    assert metrics["non_diagnostic"] is True


def test_aggregate_and_export_anonymized(isolated_db):
    from app.services.emotional_spectrum import compute_emotional_spectrum
    from app.services.emotional_spectrum_store import persist_spectrum_tick
    from app.services.dsm5_integrator import AgeGroupDataPipeline, hash_subject_id

    high = compute_emotional_spectrum(
        base_scores={"depressive": 90, "anxiety": 85, "somatic": 40},
        behavioral_metrics={
            "hesitation_index": 0.9,
            "backspace_count": 20,
            "loose_association_score": 0.7,
            "ego_boundary_loss_score": 0.6,
            "word_delay_ms": 4000,
        },
    )
    calm = compute_emotional_spectrum(
        base_scores={"depressive": 10, "anxiety": 10, "somatic": 10},
        behavioral_metrics={},
    )

    persist_spectrum_tick(
        user_id="raw-user-alice",
        session_id="sess-a",
        turn_index=1,
        result=high,
        age_group="young_adult",
        organization_id="org-hospital-1",
    )
    persist_spectrum_tick(
        user_id="raw-user-bob",
        session_id="sess-b",
        turn_index=1,
        result=calm,
        age_years=45,
        organization_id="org-hospital-1",
    )

    pipe = AgeGroupDataPipeline()
    stats = pipe.aggregate_stats(
        age_group="young_adult",
        organization_id="org-hospital-1",
        risk_cohort="any",
    )
    assert stats["ok"] is True
    assert stats["non_diagnostic"] is True
    assert stats["pii_policy"] == "fully_anonymized"
    ya = stats["cohorts"][0]
    assert ya["age_group"] == "young_adult"
    assert ya["n"] == 1
    assert ya["total_internalizing_score"]["mean"] is not None
    assert ya["total_asd_stimming_index"]["mean"] is not None
    assert "g_factor" in ya["cognitiveProfile"]
    assert ya["cognitiveProfile"]["g_factor"]["n"] == 1

    export = pipe.export_package(
        age_group="young_adult",
        risk_cohort="schizophrenia_spectrum",
        organization_id="org-hospital-1",
        limit=100,
    )
    assert export["ok"] is True
    assert export["non_diagnostic"] is True
    assert export["pii_policy"] == "fully_anonymized"
    assert export["sample_count"] >= 1
    blob = str(export)
    assert "raw-user-alice" not in blob
    assert "raw-user-bob" not in blob
    sample = export["samples"][0]
    assert sample["subject_hash"] == hash_subject_id("raw-user-alice")
    assert "user_id" not in sample
    assert "patientId" not in sample
    assert "g_factor" in sample["cognitiveProfile"]
    assert "asd_stimming_index" in sample["clinicalProfile"]
    assert "backbone_tension" in sample["threeRenderMetrics"]


def test_risk_cohort_filter(isolated_db):
    from app.services.emotional_spectrum import compute_emotional_spectrum
    from app.services.emotional_spectrum_store import persist_spectrum_tick
    from app.services.dsm5_integrator import AgeGroupDataPipeline

    calm = compute_emotional_spectrum(
        base_scores={"depressive": 5, "anxiety": 5, "somatic": 5},
        behavioral_metrics={},
    )
    persist_spectrum_tick(
        user_id="calm-user",
        session_id="sess-c",
        result=calm,
        age_group="young_adult",
        organization_id="org-h",
    )
    pipe = AgeGroupDataPipeline()
    export = pipe.export_package(
        age_group="young_adult",
        risk_cohort="high_internalizing",
        organization_id="org-h",
    )
    assert export["ok"] is True
    assert export["sample_count"] == 0


def test_verify_research_access(monkeypatch):
    from app.services.dsm5_integrator import verify_research_access

    monkeypatch.delenv("RESEARCH_EXPORT_TOKEN", raising=False)
    monkeypatch.delenv("PURGE_AUDIT_TOKEN", raising=False)
    assert verify_research_access(research_token=None, org_id=None) is False
    assert verify_research_access(research_token=None, org_id="org-1") is True

    monkeypatch.setenv("RESEARCH_EXPORT_TOKEN", "secret-token")
    assert verify_research_access(research_token="wrong", org_id="org-1") is False
    assert verify_research_access(research_token="secret-token", org_id=None) is True


def test_persist_stores_age_group_and_metrics(isolated_db):
    from app.services.emotional_spectrum import compute_emotional_spectrum
    from app.services.emotional_spectrum_store import list_spectrum_history, persist_spectrum_tick

    result = compute_emotional_spectrum(
        base_scores={"depressive": 40, "anxiety": 40, "somatic": 40},
        behavioral_metrics={},
    )
    persist_spectrum_tick(
        user_id="u-age",
        session_id="s-age",
        result=result,
        age_years=16,
    )
    history = list_spectrum_history("u-age", session_id="s-age")
    assert len(history) == 1
    assert history[0]["ageGroup"] == "adolescent"
    metrics = history[0]["metrics"]
    assert "cognitiveProfile" in metrics
    assert "g_factor" in metrics["cognitiveProfile"]
