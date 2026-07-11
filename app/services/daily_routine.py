from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.db.database import get_connection, init_db
from app.services.mood_dimensions import (
    build_mood_agent_profile,
    build_mood_portrait,
    build_sphere_visual,
    composite_mood_score,
    compute_dimension_trends,
    default_dimensions_from_score,
    dimension_meta_for_client,
    dimension_summary,
    dimensions_from_json,
    dimensions_to_json,
    normalize_dimensions,
)
from app.services.persistence import ensure_user


def _today_kst() -> date:
    return datetime.now(timezone(timedelta(hours=9))).date()


def _date_str(d: date) -> str:
    return d.isoformat()


MOOD_LABELS = {
    1: "매우 힘듦",
    2: "힘듦",
    3: "보통",
    4: "괜찮음",
    5: "좋음",
}


def _checkin_payload(
    mood_score: int,
    note: str,
    checkin_date: str,
    dimensions: Dict[str, int],
) -> Dict[str, Any]:
    dims = normalize_dimensions(dimensions)
    agent = build_mood_agent_profile(dims, mood_score)
    portrait = build_mood_portrait(dims)
    return {
        "mood_score": mood_score,
        "mood_label": MOOD_LABELS.get(mood_score, "보통"),
        "note": note,
        "checkin_date": checkin_date,
        "dimensions": dims,
        "dimension_summary": dimension_summary(dims),
        "mood_portrait": portrait,
        "agent": agent.to_dict(),
        "sphere": build_sphere_visual(dims),
    }


def record_checkin(
    user_id: str,
    mood_score: Optional[int] = None,
    note: str = "",
    dimensions: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    init_db()
    ensure_user(user_id)
    dims = normalize_dimensions(dimensions) if dimensions else None
    if dims:
        mood_score = composite_mood_score(dims)
    elif mood_score is not None:
        mood_score = max(1, min(5, int(mood_score)))
        dims = default_dimensions_from_score(mood_score)
    else:
        mood_score = 3
        dims = default_dimensions_from_score(mood_score)
    today = _date_str(_today_kst())
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO mood_checkins (user_id, mood_score, note, checkin_date, dimensions_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, checkin_date) DO UPDATE SET
                mood_score = excluded.mood_score,
                note = excluded.note,
                dimensions_json = excluded.dimensions_json,
                created_at = datetime('now')
            """,
            (user_id, mood_score, (note or "").strip(), today, dimensions_to_json(dims)),
        )
        conn.commit()
    finally:
        conn.close()
    streak = compute_streak(user_id)
    payload = _checkin_payload(mood_score, note, today, dims)
    payload.update({"user_id": user_id, "streak_days": streak["current_streak"]})
    return payload


def compute_streak(user_id: str) -> Dict[str, int]:
    init_db()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT checkin_date FROM mood_checkins
            WHERE user_id = ?
            ORDER BY checkin_date DESC
            """,
            (user_id,),
        ).fetchall()
        if not rows:
            return {"current_streak": 0, "longest_streak": 0}

        dates = sorted({date.fromisoformat(r["checkin_date"]) for r in rows}, reverse=True)
        today = _today_kst()
        current = 0
        cursor = today
        date_set = set(dates)
        while cursor in date_set:
            current += 1
            cursor -= timedelta(days=1)
        if today not in date_set and (today - timedelta(days=1)) in date_set:
            cursor = today - timedelta(days=1)
            current = 0
            while cursor in date_set:
                current += 1
                cursor -= timedelta(days=1)

        longest = 0
        run = 0
        prev: Optional[date] = None
        for d in sorted(dates):
            if prev and (d - prev).days == 1:
                run += 1
            else:
                run = 1
            longest = max(longest, run)
            prev = d
        return {"current_streak": current, "longest_streak": longest}
    finally:
        conn.close()


def recent_checkins(user_id: str, days: int = 7) -> List[Dict[str, Any]]:
    init_db()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT mood_score, note, checkin_date, created_at, dimensions_json
            FROM mood_checkins
            WHERE user_id = ?
            ORDER BY checkin_date DESC
            LIMIT ?
            """,
            (user_id, days),
        ).fetchall()
        result = []
        for row in rows:
            raw_json = row["dimensions_json"] if "dimensions_json" in row.keys() else None
            if raw_json and str(raw_json).strip() not in ("", "{}"):
                dims = dimensions_from_json(str(raw_json))
            else:
                dims = default_dimensions_from_score(row["mood_score"])
            result.append(
                _checkin_payload(row["mood_score"], row["note"], row["checkin_date"], dims)
            )
        return result
    finally:
        conn.close()


def today_checkin(user_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    today = _date_str(_today_kst())
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT mood_score, note, checkin_date, dimensions_json FROM mood_checkins
            WHERE user_id = ? AND checkin_date = ?
            """,
            (user_id, today),
        ).fetchone()
        if not row:
            return None
        dims_raw = row["dimensions_json"] if "dimensions_json" in row.keys() else None
        if dims_raw and str(dims_raw).strip() not in ("", "{}"):
            dims = dimensions_from_json(str(dims_raw))
        else:
            dims = default_dimensions_from_score(row["mood_score"])
        return _checkin_payload(row["mood_score"], row["note"], row["checkin_date"], dims)
    finally:
        conn.close()


def build_dashboard(user_id: str) -> Dict[str, Any]:
    from app.services.insights import build_weekly_report
    from app.services.persistence import list_tarot_draws, load_latest_session_for_user

    streak = compute_streak(user_id)
    checkins = recent_checkins(user_id, 7)
    today = today_checkin(user_id)
    session = load_latest_session_for_user(user_id)
    tarot = list_tarot_draws(user_id, 3)
    weekly = build_weekly_report(user_id)
    dimension_trends = compute_dimension_trends(checkins)

    greeting = "오늘도 잠깐, 마음을 입체적으로 들여다볼까요?"
    if today:
        agent_label = (today.get("agent") or {}).get("label", "")
        portrait = today.get("mood_portrait") or {}
        if portrait.get("narrative"):
            greeting = portrait["narrative"].replace("**", "")
        elif today["mood_score"] <= 2:
            greeting = f"힘든 하루일 수 있어요. {agent_label or '위로'} 모드로 천천히 함께해요."
        elif today["mood_score"] >= 4:
            greeting = f"오늘 마음이 조금 가벼워 보여요. {agent_label or '성장'} 모드로 이어가 봐요."
        elif agent_label:
            greeting = f"오늘은 {agent_label} 모드로 맞춰 드릴게요."

    return {
        "user_id": user_id,
        "greeting": greeting,
        "today_checkin": today,
        "streak": streak,
        "recent_checkins": checkins,
        "dimension_meta": dimension_meta_for_client(),
        "dimension_trends": dimension_trends,
        "session_id": session.session_id if session else None,
        "counseling_phase": session.counseling_phase if session else None,
        "homework_pending": bool(session and session.pending_homework),
        "recent_tarot": tarot,
        "weekly_report": weekly,
    }


def build_daily_context_block(user_id: str) -> str:
    """P2 — inject into chat system prompt."""
    today = today_checkin(user_id)
    recent = recent_checkins(user_id, 3)
    lines = ["[사용자 마음 루틴 컨텍스트]"]
    if today:
        lines.append(
            f"- 오늘 입체 체크인: {today.get('dimension_summary') or today['mood_score']}"
            + (f" — \"{today['note']}\"" if today.get("note") else "")
        )
        portrait = today.get("mood_portrait") or {}
        if portrait.get("narrative"):
            lines.append(f"- 마음 초상: {portrait['narrative'].replace('**', '')}")
        if portrait.get("highlights"):
            lines.append(f"- 눈에 띄는 축: {', '.join(portrait['highlights'][:3])}")
        agent = today.get("agent") or {}
        if agent.get("label"):
            lines.append(f"- 맞춤 AI 에이전트: {agent['label']} ({agent.get('focus', '')})")
    if len(recent) >= 2:
        scores = [c["mood_score"] for c in recent[:3]]
        avg = sum(scores) / len(scores)
        trend = "안정" if max(scores) - min(scores) <= 1 else ("상승" if scores[0] >= scores[-1] else "하락")
        lines.append(f"- 최근 {len(scores)}일 평균 기분: {avg:.1f}/5, 추세: {trend}")
    streak = compute_streak(user_id)
    if streak["current_streak"] >= 2:
        lines.append(f"- 연속 체크인 {streak['current_streak']}일째")
    if len(lines) == 1:
        return ""
    lines.append("- 어제/최근 기록을 자연스럽게 이어 대화하세요. 처음 보는 사람처럼 시작하지 마세요.")
    return "\n".join(lines)
