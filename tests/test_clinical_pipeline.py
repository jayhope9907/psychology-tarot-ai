"""Tests for DSM-5 screening framework and clinical pipeline."""
from __future__ import annotations

import pytest

from app.db.database import reset_db
from app.services.chat_session import ChatSessionState
from app.services.clinical_pipeline import (
    backfill_user_profile,
    extract_tarot_signals,
    get_user_psych_profile,
    sync_after_counseling,
    sync_after_tarot,
)
from app.services.dsm5_framework import list_dsm5_catalog, recommendations_from_spectra, score_text_against_spectra
from app.services.persistence import record_tarot_draw, save_session
from app.services.psych_timeline import list_events, load_profile
from app.services.tarot_bridge import apply_tarot_handoff, build_tarot_handoff


@pytest.fixture(autouse=True)
def clean_db():
    reset_db()
    yield
    reset_db()


def test_dsm5_catalog_includes_theories_and_spectra():
    catalog = list_dsm5_catalog()
    assert catalog["spectrum_count"] >= 10
    assert catalog["theory_count"] >= 15
    assert "disclaimer" in catalog
    assert any(s["spectrum_id"] == "anxiety_disorders" for s in catalog["spectra"])


def test_score_text_detects_anxiety_keywords():
    scores = score_text_against_spectra("요즘 불안하고 걱정이 많아요")
    assert scores.get("anxiety_disorders", 0) > 0.15


def test_tarot_handoff_merges_quant_features():
    handoff = {
        "user_story": "관계가 힘들고 불안해요",
        "psychology_themes": ["불안", "관계"],
        "cards": [{"psychology_theme": "불안", "meaning": "걱정", "archetype": "Hermit", "name_ko": "은둔자"}],
        "reading_summary": "마음이 무거워 보여요",
    }
    state = ChatSessionState(user_id="u1", session_id="s1")
    apply_tarot_handoff(state, handoff)
    assert "tarot_spectrum_signals" in state.quant_features
    assert state.quant_features.get("tarot_primary_spectrum")


def test_sync_after_tarot_records_timeline():
    handoff = build_tarot_handoff(
        "잠을 못 자고 우울해요",
        {"cards": [{"name_ko": "별", "psychology_theme": "희망", "meaning_ko": "회복"}]},
        {"summary": "회복의 가능성", "psychology_themes": ["우울"]},
    )
    profile = sync_after_tarot("user-tarot", "sess-1", handoff)
    assert profile["pipeline_stages"]["tarot_exploration"] is True
    events = list_events("user-tarot", 5)
    assert any(e["event_type"] == "tarot_exploration" for e in events)


def test_sync_after_counseling_builds_recommendations():
    state = ChatSessionState(user_id="user-c", session_id="sess-c")
    state.messages = [
        {"role": "user", "content": "요즘 불안하고 잠도 잘 못 자요"},
        {"role": "assistant", "content": "많이 힘드셨겠어요"},
    ]
    state.turn_count = 2
    profile = sync_after_counseling("user-c", state)
    assert profile["pipeline_stages"]["counseling"] is True
    recs = profile["recommendations"]
    assert recs.get("instruments") or recs.get("top_spectra")


def test_backfill_from_tarot_and_session():
    record_tarot_draw(
        "user-bf",
        {
            "spread": "three_card",
            "cards": [{"name_ko": "검 3", "psychology_theme": "불안", "meaning_ko": "걱정"}],
        },
    )
    state = ChatSessionState(user_id="user-bf", session_id="sess-bf")
    state.messages = [{"role": "user", "content": "우울하고 무기력해요"}]
    state.turn_count = 1
    save_session(state)

    profile = backfill_user_profile("user-bf")
    assert profile["backfill_stats"]["events_written"] >= 2
    assert profile["pipeline_stages"]["counseling"] is True
    stored = load_profile("user-bf")
    assert stored is not None
    assert stored.get("domain_scores")


def test_psych_profile_api_shape_via_service():
    profile = get_user_psych_profile("empty-user", auto_backfill=False)
    assert profile.get("empty") is True

    scores = {"anxiety_disorders": 0.6, "sleep_wake": 0.4}
    recs = recommendations_from_spectra(scores)
    assert recs["instruments"]
    assert recs["techniques"]
