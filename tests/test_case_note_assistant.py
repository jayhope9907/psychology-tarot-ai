"""케이스 노트 AI · 백데이팅 · 라이선스 게이트 테스트."""
from __future__ import annotations

from datetime import date, timedelta

from app.db.database import reset_db
from app.models.association import AssociationDiscipline, LicenseTier
from app.services.association_licensing import resolve_entitlements
from app.services.case_note_assistant import (
    entitlements_allow_assistant,
    list_journal_entries,
    process_clover_pipeline,
    resolve_event_at,
    seed_backdated_case_notes_for_demo,
    transcribe_audio,
)
import io


def test_entitlements_enable_case_notes():
    ent = resolve_entitlements(AssociationDiscipline.CLINICAL_PSYCH_TRAINEE.value, LicenseTier.SOCIETY.value)
    assert entitlements_allow_assistant(ent) is True
    assert ent["feature_flags"]["case_note_backdate"] is True


def test_backdate_blocked_without_flag():
    ent = {"feature_flags": {"case_note_assistant": True, "case_note_backdate": False}}
    timing = resolve_event_at((date.today() - timedelta(days=3)).isoformat(), ent)
    assert timing["backdated"] is False
    assert timing.get("backdate_blocked") is True


def test_pipeline_saves_backdated_notes():
    reset_db()
    ent = resolve_entitlements(AssociationDiscipline.COUNSELING.value, LicenseTier.SOCIETY.value)
    day = (date.today() - timedelta(days=4)).isoformat()
    result = process_clover_pipeline(
        user_id="user-clover-1",
        transcript="내담자: 힘들어요. 상담자: 어떤 마음이 가장 크세요?",
        entitlements=ent,
        client=None,
        backdate_to=day,
        save=True,
    )
    assert result["ok"] is True
    assert result["timing"]["backdated"] is True
    entries = list_journal_entries("user-clover-1")
    types = {e["entry_type"] for e in entries}
    assert "case_note" in types
    assert "observation_journal" in types
    assert "session_transcript" in types


def test_pipeline_requires_license():
    reset_db()
    result = process_clover_pipeline(
        user_id="user-no-lic",
        transcript="hello",
        entitlements=None,
        save=False,
    )
    assert result["ok"] is False


def test_transcribe_stub_without_client():
    out = transcribe_audio(io.BytesIO(b"fake"), filename="a.webm", client=None)
    assert out["fallback"] is True
    assert "내담자" in out["transcript"]


def test_seed_backdated_notes_for_demo():
    reset_db()
    ent = resolve_entitlements(AssociationDiscipline.MH_SOCIAL_WORK.value, LicenseTier.SOCIETY.value)
    created = seed_backdated_case_notes_for_demo("user-seed-notes", ent, backfill_days=14)
    assert len(created) >= 1
    assert list_journal_entries("user-seed-notes")
