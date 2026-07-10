from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.db.database import get_connection, init_db
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


def record_checkin(user_id: str, mood_score: int, note: str = "") -> Dict[str, Any]:
    init_db()
    ensure_user(user_id)
    mood_score = max(1, min(5, int(mood_score)))
    today = _date_str(_today_kst())
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO mood_checkins (user_id, mood_score, note, checkin_date)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, checkin_date) DO UPDATE SET
                mood_score = excluded.mood_score,
                note = excluded.note,
                created_at = datetime('now')
            """,
            (user_id, mood_score, (note or "").strip(), today),
        )
        conn.commit()
    finally:
        conn.close()
    streak = compute_streak(user_id)
    return {
        "user_id": user_id,
        "mood_score": mood_score,
        "mood_label": MOOD_LABELS.get(mood_score, "보통"),
        "note": note,
        "checkin_date": today,
        "streak_days": streak["current_streak"],
    }


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
            SELECT mood_score, note, checkin_date, created_at
            FROM mood_checkins
            WHERE user_id = ?
            ORDER BY checkin_date DESC
            LIMIT ?
            """,
            (user_id, days),
        ).fetchall()
        return [
            {
                "mood_score": row["mood_score"],
                "mood_label": MOOD_LABELS.get(row["mood_score"], "보통"),
                "note": row["note"],
                "checkin_date": row["checkin_date"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def today_checkin(user_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    today = _date_str(_today_kst())
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT mood_score, note, checkin_date FROM mood_checkins
            WHERE user_id = ? AND checkin_date = ?
            """,
            (user_id, today),
        ).fetchone()
        if not row:
            return None
        return {
            "mood_score": row["mood_score"],
            "mood_label": MOOD_LABELS.get(row["mood_score"], "보통"),
            "note": row["note"],
            "checkin_date": row["checkin_date"],
        }
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

    greeting = "오늘도 잠깐, 마음을 들여다볼까요?"
    if today:
        if today["mood_score"] <= 2:
            greeting = "힘든 하루일 수 있어요. 천천히 함께해요."
        elif today["mood_score"] >= 4:
            greeting = "오늘 마음이 조금 가벼워 보여요. 이 흐름을 이어가 봐요."

    return {
        "user_id": user_id,
        "greeting": greeting,
        "today_checkin": today,
        "streak": streak,
        "recent_checkins": checkins,
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
            f"- 오늘 기분 체크인: {today['mood_score']}/5 ({today['mood_label']})"
            + (f" — \"{today['note']}\"" if today.get("note") else "")
        )
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
