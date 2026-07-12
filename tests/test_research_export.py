"""연구 export · 정부지원 KPI · 발명 카탈로그 테스트."""
from __future__ import annotations

from app.db.database import reset_db
from app.services.research_export import (
    build_grant_kpis,
    build_innovation_catalog,
    build_research_export,
    list_inventions,
    research_consent_document,
)


def test_research_consent_is_non_diagnostic():
    doc = research_consent_document()
    assert "진단" in " ".join(doc["non_claims"])
    assert doc["schema_version"]


def test_inventions_catalog_has_five():
    items = list_inventions()
    assert len(items) >= 5
    ids = {i["id"] for i in items}
    assert "INV-01" in ids
    assert "INV-02" in ids


def test_export_requires_consent():
    reset_db()
    blocked = build_research_export(research_consent=False)
    assert blocked["ok"] is False
    assert blocked["error"] == "research_consent_required"

    ok = build_research_export(research_consent=True, limit=10)
    assert ok["ok"] is True
    assert "codebook" in ok
    assert "sessions" in ok["records"]


def test_grant_kpis_non_efficacy_framework():
    reset_db()
    kpis = build_grant_kpis()
    assert kpis["framework"] == "non_efficacy_engagement_safety"
    assert "mean_turns_per_session" in kpis["kpis"]
    assert kpis["kpis"]["invention_count"] >= 5


def test_innovation_api_shape():
    catalog = build_innovation_catalog()
    assert catalog["research"]["kpis"].endswith("grant-kpis")
    assert "/innovation" in catalog["docs"]["innovation_ui"]
