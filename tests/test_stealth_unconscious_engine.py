import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    db = tmp_path / "stealth.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    from app.db import database as dbmod

    dbmod._initialized = False
    dbmod._db_path = str(db)
    dbmod.init_db(force=True)
    yield str(db)
    dbmod._initialized = False


def test_prop_catalog_covers_eleven_props():
    from app.services.stealth_unconscious_engine import PROP_TYPES, get_prop_catalog

    catalog = get_prop_catalog()
    assert catalog["count"] == 11
    assert len(PROP_TYPES) == 11
    assert [item["prop"] for item in catalog["props"]] == PROP_TYPES
    assert catalog["chc_axes"] == ["Gv", "Gs", "Gwm", "Gc"]
    assert catalog["non_diagnostic"] is True


def test_evaluator_matches_ts_coefficients():
    from app.services.stealth_unconscious_engine import Master11PropEvaluator

    ev = Master11PropEvaluator()

    rain = ev.evaluate_rain_drop({"strobePrecisionDeltaPx": 2.0, "tremorVector": {"x": 3, "y": 4}})
    assert rain["ocdRigidity"] == pytest.approx(100 - 2.0 * 8.5)
    assert rain["panicAnxiety"] == pytest.approx(min(100, 5 * 18.2))
    assert rain["gvContribution"] == pytest.approx(100 - 2.0 * 4.2)

    tank = ev.evaluate_water_tank({"qteLatencyMs": 350, "panicStimmingCount": 4})
    assert tank["panicIndex"] == pytest.approx(38.0)
    assert tank["stimmingRate"] == 4
    assert tank["gwmContribution"] == pytest.approx(100 * math.exp(-0.0018 * 200))

    card = ev.evaluate_card_stealth({"stealthPassLatencyMs": 120, "trajectoryAccuracyRatio": 0.9})
    assert card["gsContribution"] == pytest.approx(100.0)
    assert card["gvContribution"] == pytest.approx(90.0)

    box = ev.evaluate_chamber_box({"rigidPatternRepeatCount": 2, "dimensionReconstructTimeSec": 10})
    assert box["cognitiveFlexibility"] == pytest.approx(100 - (2 * 14.5 + 10 * 1.8))
    assert box["gcContribution"] == pytest.approx(95 - 18.0)

    mirror = ev.evaluate_mirror_shadow({"illusionChasingClicks": 3, "idleAcceptanceDurationMs": 1500})
    assert mirror["dissociationScore"] == pytest.approx(49.5)
    assert mirror["realityTestingScore"] == pytest.approx(50.0)

    roulette = ev.evaluate_roulette_dial({"misdirectionBaitClicks": 1, "entropyRandomnessIndex": 0.8})
    assert roulette["impulsivityIndex"] == pytest.approx(22.0 + 0.2 * 30.0)
    assert roulette["gcContribution"] == pytest.approx(80.0)

    hologram = ev.evaluate_hologram_reality(
        {"distortionIllusionChasingClicks": 2, "perceptualRealityTestingScore": 90}
    )
    assert hologram["perceptualDefusionIndex"] == pytest.approx(66.0)

    sync = ev.evaluate_interpersonal_sync(
        {"interpersonalSyncDeltaMs": 50, "socialAdaptabilityRatio": 0.9}
    )
    assert sync["interpersonalSynchrony"] == pytest.approx(90.0)
    assert sync["gwmContribution"] == pytest.approx(90.0)


def test_defaults_are_used_for_missing_fields():
    from app.services.stealth_unconscious_engine import Master11PropEvaluator

    ev = Master11PropEvaluator()
    # 결측/비정상 값이 와도 기본값으로 폴백하고 0~100 범위를 유지
    assert 0.0 <= ev.evaluate_rain_drop({})["ocdRigidity"] <= 100.0
    assert ev.evaluate_sleight_palming({"gestureCurvatureVariance": None})[
        "fineMotorControlIndex"
    ] == pytest.approx(100 - (0.5 * 40 + 0.4 * 50))
    assert 0.0 <= ev.evaluate_mental_priming({"decisionHesitationMs": "bad"})["gcContribution"] <= 100.0


def test_full_engine_reality_architect_persona():
    from app.services.stealth_unconscious_engine import FullUnconsciousEngine

    engine = FullUnconsciousEngine()
    for _ in range(4):
        engine.ingest_biomarker(
            {"prop": "RAIN_DROP", "timestampMs": 1, "strobePrecisionDeltaPx": 0.5}
        )
        engine.ingest_biomarker(
            {
                "prop": "CARD_STEALTH",
                "timestampMs": 2,
                "stealthPassLatencyMs": 120,
                "trajectoryAccuracyRatio": 1.0,
            }
        )
        engine.ingest_biomarker(
            {
                "prop": "HOLOGRAM_REALITY",
                "timestampMs": 3,
                "perceptualRealityTestingScore": 98,
                "distortionIllusionChasingClicks": 0,
            }
        )

    result = engine.finalize_persona_assessment()
    assert result["persona"] == "DANIEL_ATLAS"
    assert "현실 검증의 설계자" in result["title"]
    assert result["awakeningLocked"] is True  # unique props < 8
    assert result["assessmentStatus"] == "provisional"
    assert result["title"].startswith("잠정")
    assert result["stats"]["perceptualRealityTesting"] > 75
    assert result["chcProfile"]["Gv"] > 80
    assert "CLINICAL IDE :: STEALTH PARSING REPORT" in result["clinicalIDEOutput"]
    assert "PROVISIONAL" in result["clinicalIDEOutput"]
    assert "non-diagnostic" in result["clinicalIDEOutput"]
    assert result["non_diagnostic"] is True


def test_full_engine_synchro_mentalist_persona():
    from app.services.stealth_unconscious_engine import evaluate_biomarker_stream

    result = evaluate_biomarker_stream(
        [
            {
                "prop": "INTERPERSONAL_SYNC",
                "timestampMs": 1,
                "interpersonalSyncDeltaMs": 40,
                "socialAdaptabilityRatio": 0.95,
            },
            {
                "prop": "PERSONA_MASK",
                "timestampMs": 2,
                "microExpressionScanLatencyMs": 200,
                "maskMatchAccuracyRatio": 0.95,
            },
        ]
    )
    assert result["persona"] == "MERRITT_MCKINNEY"
    assert result["stats"]["interpersonalSynergy"] >= 75
    assert result["assessmentStatus"] == "provisional"
    assert result["awakeningLocked"] is True
    assert result["intake"]["accepted"] == ["INTERPERSONAL_SYNC", "PERSONA_MASK"]
    assert result["intake"]["rejected"] == []


def test_final_awakening_requires_eight_unique_props():
    from app.services.stealth_unconscious_engine import FINAL_MIN_PROPS, PROP_TYPES, FullUnconsciousEngine

    assert FINAL_MIN_PROPS == 8
    engine = FullUnconsciousEngine()
    # 8개 고유 프롭을 중간 성과로 채우면 final
    payloads = [
        {"prop": "RAIN_DROP", "timestampMs": 1, "strobePrecisionDeltaPx": 2},
        {"prop": "WATER_TANK", "timestampMs": 2, "qteLatencyMs": 200, "panicStimmingCount": 0},
        {"prop": "CARD_STEALTH", "timestampMs": 3, "stealthPassLatencyMs": 150, "trajectoryAccuracyRatio": 0.9},
        {"prop": "CHAMBER_BOX", "timestampMs": 4, "rigidPatternRepeatCount": 0, "dimensionReconstructTimeSec": 8},
        {"prop": "MIRROR_SHADOW", "timestampMs": 5, "illusionChasingClicks": 0, "idleAcceptanceDurationMs": 3000},
        {"prop": "ROULETTE_DIAL", "timestampMs": 6, "misdirectionBaitClicks": 0, "entropyRandomnessIndex": 0.9},
        {"prop": "PERSONA_MASK", "timestampMs": 7, "microExpressionScanLatencyMs": 220, "maskMatchAccuracyRatio": 0.9},
        {"prop": "SLEIGHT_PALMING", "timestampMs": 8, "gestureCurvatureVariance": 0.1, "touchPressureInstability": 0.05},
    ]
    for p in payloads:
        engine.ingest_biomarker(p)
    result = engine.finalize_persona_assessment()
    assert result["progress"]["uniquePropCount"] == 8
    assert result["assessmentStatus"] == "final"
    assert result["awakeningLocked"] is False
    assert not result["title"].startswith("잠정")
    assert len(PROP_TYPES) == 11


def test_org_history_requires_license(isolated_db):
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    res = client.get("/api/v1/orgs/org-x/stealth-unconscious/history")
    assert res.status_code == 403
    body = res.json()
    msg = body.get("detail") or (body.get("error") or {}).get("message")
    assert msg == "license_required"


def test_full_engine_escape_artist_default_and_progress():
    from app.services.stealth_unconscious_engine import evaluate_biomarker_stream

    result = evaluate_biomarker_stream(
        [
            {"prop": "WATER_TANK", "timestampMs": 1, "qteLatencyMs": 2400, "panicStimmingCount": 7},
            {"prop": "not_a_prop", "timestampMs": 2},
        ]
    )
    assert result["persona"] == "HENLEY_REEVES"
    assert result["progress"]["ingested"] == ["WATER_TANK"]
    assert len(result["progress"]["remaining"]) == 10
    assert result["progress"]["completionRatio"] == pytest.approx(1 / 11, abs=1e-4)
    assert result["intake"]["rejected"] == ["not_a_prop"]
    assert result["clinicalProfile"]["panicAnxietyIndex"] > 0


def test_engine_resume_from_snapshot():
    from app.services.stealth_unconscious_engine import FullUnconsciousEngine

    first = FullUnconsciousEngine()
    first.ingest_biomarker(
        {"prop": "SLEIGHT_PALMING", "timestampMs": 1, "gestureCurvatureVariance": 0.1,
         "touchPressureInstability": 0.05}
    )
    snapshot = first.snapshot()
    assert snapshot["ingestedProps"] == ["SLEIGHT_PALMING"]

    second = FullUnconsciousEngine(
        chc=snapshot["chcProfile"],
        clinical=snapshot["clinicalProfile"],
        ingested_props=snapshot["ingestedProps"],
    )
    second.ingest_biomarker(
        {"prop": "CARD_STEALTH", "timestampMs": 2, "stealthPassLatencyMs": 130,
         "trajectoryAccuracyRatio": 0.9}
    )
    result = second.finalize_persona_assessment()
    assert result["persona"] == "JACK_WILDER"
    assert "초감각 손놀림" in result["title"]
    assert result["awakeningLocked"] is True
    assert result["progress"]["ingested"] == ["CARD_STEALTH", "SLEIGHT_PALMING"]
    assert result["clinicalProfile"]["fineMotorControlIndex"] > 80


def test_bridge_to_integrated_diagnostic_model():
    from app.services.stealth_unconscious_engine import (
        evaluate_biomarker_stream,
        to_integrated_diagnostic_model_from_persona,
    )

    fragmented = evaluate_biomarker_stream(
        [
            {"prop": "MIRROR_SHADOW", "timestampMs": 1, "illusionChasingClicks": 6},
            {
                "prop": "HOLOGRAM_REALITY",
                "timestampMs": 2,
                "perceptualRealityTestingScore": 20,
                "distortionIllusionChasingClicks": 1,
            },
            {"prop": "RAIN_DROP", "timestampMs": 3, "strobePrecisionDeltaPx": 0.4},
        ]
    )
    model = to_integrated_diagnostic_model_from_persona(
        fragmented, session_id="sess-1", patient_id="pat-1"
    )
    assert model["sessionId"] == "sess-1"
    assert model["patientId"] == "pat-1"
    cog = model["cognitiveProfile"]
    for key in (
        "g_factor",
        "crystallized_gc",
        "fluid_gf",
        "working_memory_gwm",
        "processing_speed_gs",
        "visual_processing_gv",
    ):
        assert 0.0 <= cog[key] <= 150.0
    clinical = model["clinicalProfile"]
    assert clinical["schizophrenia_index"] > 50  # 해리 + 낮은 현실검증력 → 파편화 렌더
    render = model["threeRenderMetrics"]
    assert 0.0 <= render["backbone_tension"] <= 100.0
    assert 0.0 <= render["cluster_density"] <= 100.0
    assert model["non_diagnostic"] is True


def test_persist_and_history(isolated_db):
    from app.services.stealth_unconscious_engine import evaluate_biomarker_stream
    from app.services.stealth_unconscious_store import (
        get_user_last_stealth,
        list_org_stealth_history,
        list_stealth_history,
        persist_stealth_assessment,
    )

    result = evaluate_biomarker_stream(
        [{"prop": "CHAMBER_BOX", "timestampMs": 1, "rigidPatternRepeatCount": 5,
          "dimensionReconstructTimeSec": 30}]
    )
    record = persist_stealth_assessment(
        user_id="su-user",
        session_id="su-sess",
        turn_index=2,
        result=result,
        organization_id="org-su",
    )
    assert record["id"] > 0
    assert record["persona"] in {
        "DANIEL_ATLAS",
        "MERRITT_MCKINNEY",
        "JACK_WILDER",
        "HENLEY_REEVES",
    }

    history = list_stealth_history("su-user", session_id="su-sess")
    assert len(history) == 1
    assert history[0]["chcProfile"]["Gc"] == result["chcProfile"]["Gc"]
    assert history[0]["non_diagnostic"] is True

    latest = get_user_last_stealth("su-user")
    assert latest and latest["persona"] == record["persona"]

    org_history = list_org_stealth_history("org-su")
    assert len(org_history) == 1
    assert "userId" not in org_history[0]
    assert len(org_history[0]["userIdHash"]) == 16


def test_stealth_api_roundtrip(isolated_db):
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    props = client.get("/api/v1/stealth-unconscious/props")
    assert props.status_code == 200
    assert props.json()["count"] == 11

    res = client.post(
        "/api/v1/users/api-su-user/stealth-unconscious/ingest",
        json={
            "session_id": "api-su-sess",
            "turn_index": 1,
            "payloads": [
                {"prop": "RAIN_DROP", "timestampMs": 1, "strobePrecisionDeltaPx": 0.4},
                {
                    "prop": "HOLOGRAM_REALITY",
                    "timestampMs": 2,
                    "perceptualRealityTestingScore": 97,
                },
            ],
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["record_id"]
    assert body["persona"] in {
        "DANIEL_ATLAS",
        "MERRITT_MCKINNEY",
        "JACK_WILDER",
        "HENLEY_REEVES",
    }
    assert body["progress"]["completionRatio"] == pytest.approx(2 / 11, abs=1e-4)
    assert "g_factor" in body["integrated_diagnostic_model"]["cognitiveProfile"]
    assert body["non_diagnostic"] is True

    # 2차 호출은 직전 스냅샷을 재개해 프롭 진행률이 누적된다
    res2 = client.post(
        "/api/v1/users/api-su-user/stealth-unconscious/ingest",
        json={
            "session_id": "api-su-sess",
            "turn_index": 2,
            "payloads": [
                {
                    "prop": "INTERPERSONAL_SYNC",
                    "timestampMs": 3,
                    "interpersonalSyncDeltaMs": 60,
                    "socialAdaptabilityRatio": 0.8,
                }
            ],
        },
    )
    assert res2.status_code == 200
    assert res2.json()["progress"]["completionRatio"] == pytest.approx(3 / 11, abs=1e-4)

    latest = client.get("/api/v1/users/api-su-user/stealth-unconscious")
    assert latest.status_code == 200
    assert latest.json()["latest"]["persona"]

    hist = client.get(
        "/api/v1/users/api-su-user/stealth-unconscious/history",
        params={"session_id": "api-su-sess"},
    )
    assert hist.status_code == 200
    assert hist.json()["count"] == 2


def test_ts_contract_file_mirrors_python_engine():
    src = (ROOT / "static" / "types" / "CompleteStealthUnconsciousEngine.ts").read_text(
        encoding="utf-8"
    )
    for token in (
        "INTERPERSONAL_SYNC",
        "HOLOGRAM_REALITY",
        "Master11PropEvaluator",
        "FullUnconsciousEngine",
        "finalizePersonaAssessment",
        "toIntegratedDiagnosticModel",
        "perceptualDefusionIndex",
    ):
        assert token in src

    from app.services.stealth_unconscious_engine import PROP_TYPES, default_clinical_profile

    for prop in PROP_TYPES:
        assert f"'{prop}'" in src
    for key in default_clinical_profile():
        assert key in src


def test_chat_viewer_consumes_stealth_persona():
    html = (ROOT / "static" / "chat.html").read_text(encoding="utf-8")
    assert "stealth-unconscious?session_id=" in html
    assert "loadStealthPersona" in html
    assert "_personaText" in html
    assert "_mergeStealthDiagnostic" in html
    assert 'id="mn3dOpenProps"' in html
    assert "/stealth-props" in html


def test_stealth_props_game_page_exists():
    page = ROOT / "static" / "stealth-props.html"
    assert page.exists()
    src = page.read_text(encoding="utf-8")
    for prop in (
        "RAIN_DROP",
        "HOLOGRAM_REALITY",
        "INTERPERSONAL_SYNC",
        "stealth-unconscious/ingest",
    ):
        assert prop in src
    assert "prop-deck" in src
    assert "prop-card" in src


def test_chat_status_sheet_visible():
    html = (ROOT / "static" / "chat.html").read_text(encoding="utf-8")
    assert 'id="statusSheet"' in html
    assert "openStatusSheet" in html
    assert "내 상태" in html


def test_license_and_invention_registry():
    from app.services.association_licensing import feature_enabled, resolve_entitlements
    from app.services.research_export import list_inventions

    ent = resolve_entitlements("counseling", "society")
    assert feature_enabled("stealth_unconscious_engine", ent)

    ids = {inv["id"] for inv in list_inventions()}
    assert "INV-17" in ids
