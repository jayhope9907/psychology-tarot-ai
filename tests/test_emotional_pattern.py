"""UserEmotionalPattern store + analyze_personal_pattern."""
from __future__ import annotations

from app.db.database import init_db, reset_db
from app.services.chat_session import ChatSessionState
from app.services.emotional_pattern import (
    analyze_personal_pattern,
    build_user_emotional_pattern,
    personal_pattern_prompt_block,
    record_pattern_from_chat_session,
    save_emotional_pattern,
)
from app.services.chat_stream import build_chat_messages


def test_schema_and_analyze_anomaly():
    reset_db()
    init_db(force=True)
    uid = "pattern-user-1"

    # Baseline calm sessions
    for i in range(5):
        doc = build_user_emotional_pattern(
            user_id=uid,
            session_id=f"s-base-{i}",
            sud_scores={"preSessionSUD": 4.0, "postSessionSUD": 3.5},
            cognitive_metrics={
                "cognitiveDistortionFlags": ["rumination"],
                "coreWordFrequencies": ["불안"],
                "defenseMechanismFlags": ["avoidance"],
            },
            ai_intervention_effectiveness=3,
        )
        save_emotional_pattern(doc)

    # Elevated crisis-like session with black-or-white + breakup words
    crisis = build_user_emotional_pattern(
        user_id=uid,
        session_id="s-crisis",
        sud_scores={"preSessionSUD": 9.0, "postSessionSUD": 8.5},
        cognitive_metrics={
            "cognitiveDistortionFlags": ["all_or_nothing", "catastrophizing"],
            "coreWordFrequencies": ["서운", "외로", "우울"],
            "defenseMechanismFlags": ["avoidance", "denial"],
        },
        ai_intervention_effectiveness=2,
    )
    save_emotional_pattern(crisis)

    analysis = analyze_personal_pattern(uid, window=8)
    assert analysis["sampleSize"] >= 5
    assert analysis["inEmotionalCrisisVsBaseline"] is True
    assert analysis["topDistortions"]
    labels = [d["labelKo"] for d in analysis["topDistortions"]]
    assert "흑백논리" in labels or "파국화" in labels or "반추" in labels
    assert "패턴" in analysis["patternReportKo"] or "베이스라인" in analysis["patternReportKo"]

    block = personal_pattern_prompt_block(analysis)
    assert "개인 고유 정서 패턴" in block
    assert "비진단" in block


def test_record_from_session_and_prompt_binding():
    reset_db()
    init_db(force=True)
    uid = "pattern-user-2"
    # Seed a few prior sessions
    for i in range(5):
        save_emotional_pattern(
            build_user_emotional_pattern(
                user_id=uid,
                session_id=f"prior-{i}",
                sud_scores={"preSessionSUD": 5 + (i % 2), "postSessionSUD": 5},
                cognitive_metrics={
                    "cognitiveDistortionFlags": ["all_or_nothing"],
                    "coreWordFrequencies": ["연애", "서운"] if False else ["서운"],
                    "defenseMechanismFlags": ["projection"],
                },
            )
        )

    state = ChatSessionState(session_id="live-1", user_id=uid)
    state.messages = [
        {"role": "user", "content": "이별 때문에 완전 망했어요. 느끼니까 끝인 것 같아요."},
        {"role": "assistant", "content": "마음이 많이 무거우시군요."},
        {"role": "user", "content": "항상 저는 실패해요. 또 외로워요."},
    ]
    state.persona_routing = {
        "school": "CBT",
        "mood_state": "VULNERABLE",
        "detected_distortions": ["all_or_nothing"],
    }
    state.quant_features = {"psychiatric_stress_weight": 0.7}

    doc = record_pattern_from_chat_session(
        uid,
        state,
        pre_sud=8,
        post_sud=7,
        intervention_effectiveness=4,
        physical_metrics={"cardSelectionDelay": 9200, "gyroInstability": 0.45},
    )
    assert doc["userId"] == uid
    assert "all_or_nothing" in doc["cognitiveMetrics"]["cognitiveDistortionFlags"]
    assert doc["physicalMetrics"]["cardSelectionDelay"] == 9200

    analysis = analyze_personal_pattern(uid, window=8)
    block = personal_pattern_prompt_block(analysis)
    assert "개인 고유 정서 패턴" in block
    assert "흑백논리" in block or "왜곡" in block

    state.quant_features = {
        "psychological_readiness_index": 0.4,
        "tree_energy_index": 0.5,
        "psychiatric_stress_weight": 0.7,
        "attachment_matrix_score": 0.5,
        "structural_sign": "circle",
        "cognitive_distortions": ["all_or_nothing"],
    }
    messages = build_chat_messages(state, "흑백논리로 또 나 자신을 밀어붙이는 느낌이어요")
    system = messages[0]["content"]
    assert "개인 고유 정서 패턴" in system
