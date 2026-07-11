from app.services.daily_routine import record_checkin
from app.services.mood_assistant import resolve_mood_context
from app.services.mood_dimensions import (
    build_mood_agent_profile,
    build_mood_portrait,
    composite_mood_score,
    compute_dimension_trends,
    default_dimensions_from_score,
    normalize_dimensions,
    resolve_agent_mode,
)


def test_normalize_dimensions_defaults():
    dims = normalize_dimensions({})
    assert dims["valence"] == 3
    assert dims["anxiety"] == 3


def test_composite_score_weights_valence():
    low = composite_mood_score({"valence": 1, "energy": 3, "anxiety": 3, "social": 3, "sleep": 3})
    high = composite_mood_score({"valence": 5, "energy": 3, "anxiety": 3, "social": 3, "sleep": 3})
    assert low < high


def test_agent_mode_calm_for_high_anxiety():
    dims = normalize_dimensions({"valence": 3, "energy": 3, "anxiety": 5, "social": 3, "sleep": 3})
    mode = resolve_agent_mode(dims, composite_mood_score(dims))
    assert mode == "calm"


def test_agent_mode_comfort_for_low_valence():
    dims = normalize_dimensions({"valence": 1, "energy": 2, "anxiety": 2, "social": 2, "sleep": 2})
    mode = resolve_agent_mode(dims, composite_mood_score(dims))
    assert mode == "comfort"


def test_record_checkin_with_dimensions():
    user = "dim-checkin-user"
    dims = {"valence": 2, "energy": 2, "anxiety": 4, "social": 2, "sleep": 2}
    result = record_checkin(user, dimensions=dims)
    assert result["dimensions"]["anxiety"] == 4
    assert result["agent"]["mode"] in ("comfort", "calm", "restore", "connect", "rest", "growth", "balance")
    assert result["sphere"]["anxiety"] == 4


def test_resolve_mood_context_includes_agent():
    user = "dim-context-user"
    record_checkin(
        user,
        dimensions={"valence": 4, "energy": 5, "anxiety": 2, "social": 4, "sleep": 4},
    )
    ctx = resolve_mood_context(user)
    assert ctx.has_checkin is True
    assert ctx.agent is not None
    assert ctx.dimensions["energy"] == 5


def test_default_dimensions_from_score():
    dims = default_dimensions_from_score(1)
    assert dims["valence"] == 1
    assert dims["anxiety"] == 5


def test_build_mood_agent_profile_sphere():
    profile = build_mood_agent_profile(default_dimensions_from_score(3))
    assert "rotateX" in profile.sphere
    assert profile.label


def test_mood_portrait_narrative():
    dims = {"valence": 2, "energy": 2, "anxiety": 4, "social": 2, "sleep": 2}
    portrait = build_mood_portrait(dims)
    assert portrait["fingerprint"]
    assert "기분" in portrait["narrative"]
    assert len(portrait["axes"]) == 5
    assert portrait["highlights"]


def test_dimension_trends_from_checkins():
    checkins = [
        {"dimensions": {"valence": 2, "energy": 2, "anxiety": 4, "social": 2, "sleep": 2}, "mood_score": 2},
        {"dimensions": {"valence": 3, "energy": 3, "anxiety": 3, "social": 3, "sleep": 3}, "mood_score": 3},
    ]
    trends = compute_dimension_trends(checkins)
    assert trends["days"] == 2
    assert len(trends["axes"]) == 5
    assert trends["axes"][0]["latest"] >= 1
