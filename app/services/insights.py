from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List

from app.db.database import get_connection, init_db
from app.services.daily_routine import MOOD_LABELS, recent_checkins
from app.services.mood_dimensions import compute_dimension_trends
from app.services.persistence import list_tarot_draws


def _today_kst() -> date:
    return datetime.now(timezone(timedelta(hours=9))).date()


def build_weekly_report(user_id: str) -> Dict[str, Any]:
    init_db()
    checkins = recent_checkins(user_id, 7)
    tarot = list_tarot_draws(user_id, 7)
    chat_turns = _chat_turns_this_week(user_id)

    if not checkins and not tarot and not chat_turns:
        return {
            "summary": "이번 주 기록이 아직 없어요. 오늘 30초 체크인으로 시작해 보세요.",
            "avg_mood": None,
            "mood_trend": "unknown",
            "checkin_days": 0,
            "tarot_count": 0,
            "chat_turns": 0,
            "insights": [],
        }

    scores = [c["mood_score"] for c in checkins]
    avg_mood = round(sum(scores) / len(scores), 1) if scores else None
    mood_trend = "stable"
    if len(scores) >= 2:
        if scores[0] > scores[-1]:
            mood_trend = "improving"
        elif scores[0] < scores[-1]:
            mood_trend = "declining"

    card_names = []
    for draw in tarot:
        for card in draw.get("cards", []):
            card_names.append(card.get("name_ko") or card.get("name_en", ""))
    top_cards = Counter(card_names).most_common(3)

    insights: List[str] = []
    if avg_mood is not None:
        if avg_mood <= 2.5:
            insights.append("이번 주 평균 기분이 낮았어요. 짧은 대화나 타로로 마음을 풀어보는 것도 도움이 됩니다.")
        elif avg_mood >= 4:
            insights.append("이번 주 전반적으로 마음이 비교적 안정적이었어요. 이 흐름을 기록으로 남겨보세요.")
    if mood_trend == "improving":
        insights.append("최근 며칠 사이 기분이 조금 나아지고 있어요.")
    elif mood_trend == "declining":
        insights.append("최근 기분이 조금 무거워지고 있어요. 혼자 버티지 않아도 괜찮아요.")
    if top_cards:
        names = ", ".join(name for name, _ in top_cards)
        insights.append(f"자주 뽑힌 카드: {names}")

    dim_trends = compute_dimension_trends(checkins)
    if dim_trends.get("summary"):
        insights.append(f"5축 추적: {dim_trends['summary']}")
    for axis in dim_trends.get("axes", []):
        if axis.get("trend") == "rising" and axis["key"] == "anxiety":
            insights.append(f"이번 주 {axis['label']}이 점점 높아지고 있어요. 짧은 호흡·쉬는 시간을 의식해 보세요.")
        elif axis.get("trend") == "falling" and axis["key"] == "anxiety":
            insights.append(f"{axis['label']}은(는) 조금 가라앉는 추세예요.")
        elif axis.get("trend") == "rising" and axis["key"] in ("valence", "energy", "social", "sleep"):
            insights.append(f"{axis['label']}이 회복·상승하는 흐름이에요 ({axis['latest_facet']}).")
        elif axis.get("trend") == "falling" and axis["key"] in ("valence", "energy", "social", "sleep"):
            insights.append(f"{axis['label']}이 평균보다 낮아지는 편이에요. 무리하지 않는 선택을 해도 괜찮아요.")

    summary_parts = [f"체크인 {len(checkins)}일"]
    if tarot:
        summary_parts.append(f"타로 {len(tarot)}회")
    if chat_turns:
        summary_parts.append(f"상담 {chat_turns}턴")

    return {
        "summary": f"이번 주 {', '.join(summary_parts)} 기록이 있어요.",
        "avg_mood": avg_mood,
        "avg_mood_label": MOOD_LABELS.get(round(avg_mood)) if avg_mood else None,
        "mood_trend": mood_trend,
        "checkin_days": len(checkins),
        "tarot_count": len(tarot),
        "chat_turns": chat_turns,
        "top_tarot_cards": [{"name": n, "count": c} for n, c in top_cards],
        "dimension_trends": dim_trends,
        "insights": insights,
    }


def _chat_turns_this_week(user_id: str) -> int:
    init_db()
    week_ago = (_today_kst() - timedelta(days=7)).isoformat()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT state_json FROM session_snapshots
            WHERE user_id = ? AND updated_at >= ?
            """,
            (user_id, week_ago),
        ).fetchall()
        total = 0
        import json

        for row in rows:
            data = json.loads(row["state_json"])
            total += data.get("turn_count", 0)
        return total
    finally:
        conn.close()


def suggest_homework_intensity(user_id: str) -> str:
    """P4 — lighter homework when mood is low."""
    checkins = recent_checkins(user_id, 3)
    if not checkins:
        return "standard"
    avg = sum(c["mood_score"] for c in checkins) / len(checkins)
    if avg <= 2:
        return "light"
    if avg >= 4:
        return "standard"
    return "gentle"
