"""라이선스 온보딩 — 에이전트 구축 + 사례 백데이팅."""
from __future__ import annotations

from app.db.database import reset_db
from app.models.association import AssociationDiscipline, LicenseTier
from app.services.association_agent import build_association_agent
from app.services.association_context import bind_license_to_session
from app.services.association_licensing import resolve_entitlements
from app.services.chat_session import ChatSessionState
from app.services.license_store import provision_license, validate_license
from app.services.psych_timeline import list_events, load_profile


def test_build_association_agent_counseling():
    ent = resolve_entitlements(AssociationDiscipline.COUNSELING.value, LicenseTier.SOCIETY.value)
    agent = build_association_agent(ent, org_name="테스트 상담원")
    assert agent["agent_name"] == "상담 가이드"
    assert agent["preferred_school"] == "ROGERIAN"
    assert "relational" in agent["case_bias"]
    assert agent["org_name"] == "테스트 상담원"


def test_build_association_agent_psychiatry():
    ent = resolve_entitlements(AssociationDiscipline.PSYCHIATRY.value, LicenseTier.FEDERATION.value)
    agent = build_association_agent(ent)
    assert agent["preferred_school"] == "TRAUMA_INFORMED"
    assert "trauma" in agent["case_bias"]


def test_provision_license_seeds_agent_and_cases():
    reset_db()
    result = provision_license(
        "온보딩 테스트 기관",
        AssociationDiscipline.PSYCHOLOGY.value,
        LicenseTier.SOCIETY.value,
        backfill_days=21,
    )
    assert result["provisioned"] is True
    assert result["valid"] is True
    assert result.get("agent_profile", {}).get("agent_name") == "심리 탐색 가이드"
    demo_cases = result.get("demo_cases") or []
    assert len(demo_cases) >= 2
    assert all(c.get("case_id") for c in demo_cases)
    assert all(c.get("user_id") for c in demo_cases)

    # 재검증 시 메타데이터 유지
    again = validate_license(result["license_key"])
    assert again.get("agent_profile")
    assert len(again.get("demo_cases") or []) >= 2


def test_demo_case_backdated_timeline():
    reset_db()
    result = provision_license(
        "백데이팅 테스트",
        AssociationDiscipline.COUNSELING.value,
        LicenseTier.CHAPTER.value,
        case_ids=["relational"],
        backfill_days=14,
    )
    demo = (result.get("demo_cases") or [])[0]
    user_id = demo["user_id"]
    events = list_events(user_id, limit=20)
    assert len(events) >= 3
    types = {e["event_type"] for e in events}
    assert "mood_checkin" in types
    assert "counseling_session" in types
    assert "case_classification" in types

    profile = load_profile(user_id)
    assert profile
    assert profile.get("demo_case_id") == "relational"


def test_bind_license_applies_agent_to_session():
    reset_db()
    provision = provision_license(
        "바인딩 테스트",
        AssociationDiscipline.COUNSELING.value,
        LicenseTier.SOCIETY.value,
    )
    session = ChatSessionState(user_id="u-bind", session_id="s-bind")
    bound = bind_license_to_session(session, provision["license_key"], assign_user=False)
    assert bound["bound"] is True
    assert bound.get("agent_profile", {}).get("agent_name") == "상담 가이드"
    assert session.preferred_school == "ROGERIAN"
    assert session.phase_notes.get("association_agent")


def test_demo_license_gets_onboarded_on_init():
    reset_db()
    result = validate_license("MSHT-COUNSEL-DEMO-2026")
    assert result["valid"] is True
    assert result.get("agent_profile")
    assert len(result.get("demo_cases") or []) >= 2
