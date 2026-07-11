"""Tests for dream seed framing."""
from __future__ import annotations

from app.services.case_preview import build_case_preview
from app.services.chat_session import ChatSessionState
from app.services.dream_seed import build_dream_seed


def test_dream_seed_always_has_universal_acknowledgment():
    state = ChatSessionState(user_id="u-dream", session_id="s-dream")
    dream = build_dream_seed(state, "안녕하세요")
    assert dream["active"] is True
    assert "돈" in dream["acknowledgment"]
    assert dream["headline"] == "꿈을 심는 시간"
    assert len(dream["dream_prompts"]) >= 2


def test_dream_seed_stronger_for_work_money_talk():
    state = ChatSessionState(user_id="u-work", session_id="s-work")
    state.phase_notes["chief_complaint"] = "월급이 빠듯해서 퇴사하고 싶어요"
    dream = build_dream_seed(state, "직장 스트레스가 너무 커요")
    assert dream["signals"]["work_money"] >= 0.2 or dream["signals"]["work_context"] >= 0.25
    assert dream["micro_seeds"]


def test_case_preview_includes_dream_seed():
    state = ChatSessionState(user_id="u-prev", session_id="s-prev")
    preview = build_case_preview(state, "일 때문에 너무 지쳐요")
    assert "dream_seed" in preview
    assert preview["dream_seed"].get("headline")
