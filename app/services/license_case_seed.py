"""라이선스 발급 시 데모 사례·백데이팅 시드."""
from __future__ import annotations

import json
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.assessments import ALL_INSTRUMENTS
from app.models.association import AssociationDiscipline
from app.services.association_agent import DISCIPLINE_AGENT_DEFAULTS
from app.services.association_licensing import instrument_allowed
from app.services.case_preview import CASE_PROFILES, CASE_TYPE_LABELS
from app.services.chat_session import ChatSessionState
from app.services.license_store import assign_member
from app.services.persistence import ensure_user, save_session
from app.services.psych_timeline import record_event, save_profile

DISCIPLINE_DEFAULT_CASES: Dict[str, Tuple[str, ...]] = {
    AssociationDiscipline.COUNSELING.value: ("relational", "depressive", "general_distress"),
    AssociationDiscipline.PSYCHOLOGY.value: ("depressive", "anxiety", "cognitive_behavioral"),
    AssociationDiscipline.PSYCHIATRY.value: ("trauma", "anxiety", "sleep"),
    AssociationDiscipline.INTEGRATIVE.value: ("general_distress", "stress_adjustment", "relational"),
}

CASE_SEED_SCRIPTS: Dict[str, Dict[str, Any]] = {
    "relational": {
        "chief_complaint": "가까운 사람과 자꾸 멀어지는 느낌",
        "display_name": "데모 · 관계",
        "mood_score": 4,
        "user_msgs": [
            "요즘 친구·연인 관계가 예전 같지 않아요.",
            "혼자 있는 게 편한데 또 외롭고, 먼저 연락하기가 어려워요.",
        ],
        "assistant_msgs": [
            "관계에서 어떤 순간이 가장 마음에 남으세요?",
            "외로움과 거리 두기가 동시에 느껴지시는군요. 천천히 이야기해 주셔도 돼요.",
        ],
    },
    "depressive": {
        "chief_complaint": "의욕이 없고 하루가 무겁게 느껴짐",
        "display_name": "데모 · 기분",
        "mood_score": 3,
        "user_msgs": [
            "아침에 일어나기가 너무 힘들어요.",
            "예전에 좋아하던 것도 재미가 없고, 그냥 버티는 느낌이에요.",
        ],
        "assistant_msgs": [
            "하루를 시작할 때 몸과 마음이 어떤지 함께 짚어볼게요.",
            "무겁게 느껴지는 날이 반복될 때는 작은 것부터 돌봐도 괜찮아요.",
        ],
    },
    "anxiety": {
        "chief_complaint": "걱정이 멈추지 않고 몸도 긴장됨",
        "display_name": "데모 · 불안",
        "mood_score": 4,
        "user_msgs": [
            "일이 끝나도 머릿속 걱정이 계속돼요.",
            "가끔 가슴이 두근거리고 숨이 가빠질 때가 있어요.",
        ],
        "assistant_msgs": [
            "걱정이 특히 커지는 시간대나 상황이 있을까요?",
            "몸의 긴장도 함께 느껴지시는군요. 지금 이 자리에서 잠깐 숨 고를 수 있어요.",
        ],
    },
    "trauma": {
        "chief_complaint": "힘든 기억이 자꾸 떠오름",
        "display_name": "데모 · 외상",
        "mood_score": 3,
        "user_msgs": [
            "예전에 겪은 일이 문득문득 떠올라요.",
            "밤에 잠들기 어렵고, 깨면 마음이 불안해요.",
        ],
        "assistant_msgs": [
            "지금 이야기하기 부담스럽다면 속도를 천천히 맞춰도 됩니다.",
            "안전하게 느껴지는 것부터 짧게 확인해 볼 수 있어요.",
        ],
    },
    "sleep": {
        "chief_complaint": "잠들기 어렵고 낮에도 피곤함",
        "display_name": "데모 · 수면",
        "mood_score": 4,
        "user_msgs": [
            "밤에 뒤척이다 새벽에야 잠들어요.",
            "낮에도 졸리고 집중이 잘 안 돼요.",
        ],
        "assistant_msgs": [
            "수면 리듬이 언제부터 흔들렸는지 함께 볼까요?",
            "잠과 기분은 서로 영향을 주곤 해요. 부담 없이 짚어봐도 괜찮아요.",
        ],
    },
    "stress_adjustment": {
        "chief_complaint": "일·생활 스트레스가 한계",
        "display_name": "데모 · 스트레스",
        "mood_score": 4,
        "user_msgs": [
            "요즘 일이 너무 버겁고 지쳐요.",
            "쉬고 싶은데 쉴 틈이 없는 느낌이에요.",
        ],
        "assistant_msgs": [
            "어떤 부분이 가장 버거우세요?",
            "지친 신호를 알아차린 것만으로도 회복의 시작일 수 있어요.",
        ],
    },
    "cognitive_behavioral": {
        "chief_complaint": "부정적인 생각이 반복됨",
        "display_name": "데모 · 생각",
        "mood_score": 5,
        "user_msgs": [
            "일을 시작하기 전부터 잘 안 될 것 같다는 생각이 들어요.",
            "실수하면 최악일 것 같아서 미루게 돼요.",
        ],
        "assistant_msgs": [
            "자주 드는 생각 중 하나를 같이 적어볼 수 있을까요?",
            "생각과 행동이 서로 영향을 주는 패턴을 천천히 살펴볼게요.",
        ],
    },
    "general_distress": {
        "chief_complaint": "답답하고 막막한 마음",
        "display_name": "데모 · 탐색",
        "mood_score": 5,
        "user_msgs": [
            "뭐가 문제인지 잘 모르겠는데 전반적으로 힘들어요.",
            "이야기는 하고 싶은데 어디서부터 할지 막막해요.",
        ],
        "assistant_msgs": [
            "지금 마음을 한 단어로 표현한다면 어떤 느낌일까요?",
            "정확히 모르셔도 괜찮아요. 편한 만큼만 이어가 봐요.",
        ],
    },
}


def _iso_at(day: date, hour: int = 10) -> str:
    dt = datetime(day.year, day.month, day.day, hour, 0, 0, tzinfo=timezone.utc)
    return dt.isoformat()


def _pick_cases(
    discipline_id: str,
    entitlements: Dict[str, Any],
    case_ids: Optional[List[str]] = None,
    max_cases: int = 3,
) -> List[str]:
    if case_ids:
        picked = [c for c in case_ids if c in CASE_PROFILES][:max_cases]
        if picked:
            return picked
    defaults = DISCIPLINE_DEFAULT_CASES.get(
        discipline_id, DISCIPLINE_DEFAULT_CASES[AssociationDiscipline.COUNSELING.value]
    )
    agent_bias = DISCIPLINE_AGENT_DEFAULTS.get(discipline_id, {}).get("case_bias") or []
    merged: List[str] = []
    for cid in list(agent_bias) + list(defaults):
        if cid in CASE_PROFILES and cid not in merged:
            merged.append(cid)
    return merged[:max_cases]


def _seed_formal_answers(
    case_id: str,
    entitlements: Dict[str, Any],
) -> Dict[str, Dict[str, int]]:
    profile = CASE_PROFILES.get(case_id, {})
    preferred = list(profile.get("instrument_ids") or ())
    answers: Dict[str, Dict[str, int]] = {}
    for instrument_id in preferred:
        if not instrument_allowed(instrument_id, entitlements):
            continue
        if instrument_id not in ALL_INSTRUMENTS:
            continue
        items = ALL_INSTRUMENTS[instrument_id].items()
        if not items:
            continue
        # 중간~약간 높은 응답으로 스크리닝 신호 시뮬레이션
        value = 2 if case_id in ("depressive", "trauma", "anxiety") else 1
        answers[instrument_id] = {item.item_id: value for item in items[:3]}
    return answers


def _insert_mood_checkin(user_id: str, day: date, mood_score: int, note: str) -> None:
    from app.db.database import get_connection, init_db

    init_db()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO mood_checkins (user_id, mood_score, note, checkin_date, dimensions_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, checkin_date) DO UPDATE SET
                mood_score = excluded.mood_score,
                note = excluded.note
            """,
            (user_id, mood_score, note, day.isoformat(), "{}"),
        )
        conn.commit()
    finally:
        conn.close()


def seed_demo_case(
    org_id: str,
    license_key: str,
    entitlements: Dict[str, Any],
    case_id: str,
    *,
    anchor_day: date,
    backfill_days: int = 28,
    case_index: int = 0,
) -> Dict[str, Any]:
    """단일 데모 사례: 백데이팅 세션·타임라인·기분 기록."""
    script = CASE_SEED_SCRIPTS.get(case_id) or CASE_SEED_SCRIPTS["general_distress"]
    profile = CASE_PROFILES[case_id]
    user_id = f"{org_id}-case-{case_id}"
    session_id = f"s-{org_id[:12]}-{case_id}-{secrets.token_hex(3)}"
    display = script.get("display_name") or CASE_TYPE_LABELS.get(case_id, case_id)

    ensure_user(user_id, display_name=display)
    assign_member(org_id, user_id, role="demo_case")

    # 백데이팅 일정: anchor에서 역산
    span = max(7, backfill_days)
    offsets = sorted(
        {
            span,
            int(span * 0.75),
            int(span * 0.5),
            int(span * 0.25),
            max(1, 3 + case_index),
        },
        reverse=True,
    )

    events_created = 0
    for i, offset in enumerate(offsets):
        day = anchor_day - timedelta(days=offset)
        mood = max(2, min(8, script.get("mood_score", 5) - (i % 2)))
        _insert_mood_checkin(user_id, day, mood, f"[데모] {profile['label']}")
        record_event(
            user_id,
            "mood_checkin",
            {"mood_score": mood, "demo_case": case_id, "backfill": True},
            event_at=_iso_at(day, 9),
            source_id=f"seed:checkin:{case_id}:{day.isoformat()}",
        )
        events_created += 1

    # 대화 세션 (가장 최근 날짜)
    session_day = anchor_day - timedelta(days=max(1, 3 + case_index))
    messages: List[Dict[str, str]] = []
    for u, a in zip(script["user_msgs"], script["assistant_msgs"]):
        messages.append({"role": "user", "content": u})
        messages.append({"role": "assistant", "content": a})

    formal_answers = _seed_formal_answers(case_id, entitlements)
    state = ChatSessionState(
        user_id=user_id,
        session_id=session_id,
        turn_count=len(script["user_msgs"]),
        messages=messages,
        formal_answers=formal_answers,
        counseling_phase="exploration",
        phase_history=["rapport", "exploration"],
        phase_notes={
            "chief_complaint": script["chief_complaint"],
            "demo_case_id": case_id,
            "demo_case_label": profile["label"],
            "seeded_at": anchor_day.isoformat(),
            "seed_source": "license_provision",
        },
        org_id=org_id,
        org_entitlements=entitlements,
        association_license_key=license_key,
        plan=entitlements.get("plan_override") or "PLUS",
    )
    save_session(state)

    record_event(
        user_id,
        "counseling_session",
        {
            "session_id": session_id,
            "turn_count": state.turn_count,
            "chief_complaint": script["chief_complaint"],
            "demo_case_id": case_id,
            "backfill": True,
        },
        event_at=_iso_at(session_day, 14),
        source_id=f"seed:session:{session_id}",
    )
    record_event(
        user_id,
        "case_classification",
        {
            "case_id": case_id,
            "case_type": CASE_TYPE_LABELS.get(case_id, profile["label"]),
            "label": profile["label"],
            "probability": 62 - case_index * 5,
            "demo": True,
            "backfill": True,
        },
        event_at=_iso_at(session_day, 15),
        source_id=f"seed:case:{case_id}",
    )
    events_created += 2

    save_profile(
        user_id,
        {
            "user_id": user_id,
            "demo_case_id": case_id,
            "demo_case_label": profile["label"],
            "chief_complaint": script["chief_complaint"],
            "org_id": org_id,
            "license_key": license_key,
            "pipeline_stages": {
                "tarot_exploration": False,
                "counseling": True,
                "recommendations": bool(formal_answers),
            },
            "seed_backfill_days": backfill_days,
            "last_session_id": session_id,
        },
    )

    return {
        "user_id": user_id,
        "session_id": session_id,
        "case_id": case_id,
        "case_type": CASE_TYPE_LABELS.get(case_id, profile["label"]),
        "label": profile["label"],
        "chief_complaint": script["chief_complaint"],
        "events_created": events_created,
        "formal_instruments": list(formal_answers.keys()),
        "backfill_from": (anchor_day - timedelta(days=span)).isoformat(),
        "backfill_to": anchor_day.isoformat(),
    }


def seed_org_demo_cases(
    org_id: str,
    license_key: str,
    entitlements: Dict[str, Any],
    *,
    anchor_day: Optional[date] = None,
    backfill_days: int = 28,
    case_ids: Optional[List[str]] = None,
    max_cases: int = 3,
) -> Dict[str, Any]:
    """조직 라이선스용 데모 사례 일괄 시드 + 백데이팅."""
    anchor = anchor_day or date.today()
    picked = _pick_cases(
        entitlements.get("discipline_id") or AssociationDiscipline.COUNSELING.value,
        entitlements,
        case_ids=case_ids,
        max_cases=max_cases,
    )
    cases: List[Dict[str, Any]] = []
    for idx, case_id in enumerate(picked):
        cases.append(
            seed_demo_case(
                org_id,
                license_key,
                entitlements,
                case_id,
                anchor_day=anchor,
                backfill_days=backfill_days,
                case_index=idx,
            )
        )
    return {
        "org_id": org_id,
        "license_key": license_key,
        "anchor_day": anchor.isoformat(),
        "backfill_days": backfill_days,
        "case_count": len(cases),
        "demo_cases": cases,
    }


def update_license_metadata(license_key: str, patch: Dict[str, Any]) -> None:
    from app.db.database import get_connection, init_db

    init_db()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT metadata_json FROM organization_licenses WHERE license_key = ?",
            (license_key.upper(),),
        ).fetchone()
        if not row:
            raise ValueError(f"license not found: {license_key}")
        meta = json.loads(row["metadata_json"] or "{}")
        meta.update(patch)
        conn.execute(
            "UPDATE organization_licenses SET metadata_json = ? WHERE license_key = ?",
            (json.dumps(meta, ensure_ascii=False), license_key.upper()),
        )
        conn.commit()
    finally:
        conn.close()


def load_license_metadata(license_key: str) -> Dict[str, Any]:
    from app.db.database import get_connection, init_db

    init_db()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT metadata_json FROM organization_licenses WHERE license_key = ?",
            (license_key.upper(),),
        ).fetchone()
        if not row:
            return {}
        return json.loads(row["metadata_json"] or "{}")
    finally:
        conn.close()
