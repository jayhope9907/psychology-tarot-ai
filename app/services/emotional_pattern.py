"""Personal emotional pattern tracking (UserEmotionalPattern) + anomaly analysis.

SQLite-backed longitudinal store of per-session physical/cognitive/SUD signals,
plus analyze_personal_pattern() for prompt binding into counselor 이서연.
Non-diagnostic wellness framing only.
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from app.db.database import get_connection, init_db
from app.services.persistence import ensure_user

# CBT cognitive distortion codes → Korean report labels
DISTORTION_LABELS_KO: Dict[str, str] = {
    "all_or_nothing": "흑백논리",
    "overgeneralization": "과잉일반화",
    "mental_filter": "정신적 여과",
    "disqualifying_positive": "긍정 평가절하",
    "mind_reading": "독심술",
    "fortune_telling": "예언적 사고",
    "magnification": "확대·파국화",
    "catastrophizing": "파국화",
    "emotional_reasoning": "감정적 추론",
    "should_statements": "당위적 사고",
    "labeling": "낙인찍기",
    "personalization": "개인화",
    "blaming": "비난",
    "control_fallacy": "통제 오류",
    "fallacy_of_fairness": "공정성 오류",
    "always_being_right": "무조건 옳음",
    "rumination": "반추",
    "divine_punishment": "신벌·심판 과도귀인",
    "condemnation_loop": "정죄 루프",
    "works_righteousness": "행위 의로움 압박",
    "spiritual_all_or_nothing": "영적 흑백사고",
    "abandoned_by_god": "하나님 유기 감각",
    "prayer_transaction": "기도-거래 사고",
}

# Stress-situation defense mechanisms (heuristic tags)
DEFENSE_LABELS_KO: Dict[str, str] = {
    "avoidance": "회피",
    "intellectualization": "주지화",
    "projection": "투사",
    "denial": "부정",
    "rationalization": "합리화",
    "withdrawal": "철수",
}

EMOTION_CORE_WORDS = (
    "외로",
    "불안",
    "우울",
    "분노",
    "지침",
    "두려",
    "수치",
    "죄책",
    "질투",
    "그리움",
    "답답",
    "허무",
    "기쁨",
    "안심",
    "설렘",
    "미안",
    "서운",
    "억울",
    "초조",
    "무기력",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_emotional_pattern_table() -> None:
    init_db()
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS user_emotional_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL DEFAULT '',
                session_date TEXT NOT NULL,
                physical_metrics_json TEXT NOT NULL DEFAULT '{}',
                cognitive_metrics_json TEXT NOT NULL DEFAULT '{}',
                sud_scores_json TEXT NOT NULL DEFAULT '{}',
                ai_intervention_effectiveness REAL,
                pattern_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, session_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            CREATE INDEX IF NOT EXISTS idx_uep_user_date
                ON user_emotional_patterns(user_id, session_date DESC);
            """
        )
        conn.commit()
    finally:
        conn.close()


def empty_physical_metrics(
    *,
    card_selection_delay_ms: Optional[float] = None,
    gyro_instability: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "cardSelectionDelay": float(card_selection_delay_ms)
        if card_selection_delay_ms is not None
        else None,
        "gyroInstability": float(gyro_instability) if gyro_instability is not None else None,
    }


def empty_cognitive_metrics(
    *,
    distortion_flags: Optional[Sequence[str]] = None,
    core_words: Optional[Sequence[str]] = None,
    defense_flags: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    return {
        "cognitiveDistortionFlags": list(distortion_flags or []),
        "coreWordFrequencies": list(core_words or []),
        "defenseMechanismFlags": list(defense_flags or []),
    }


def empty_sud_scores(
    *,
    pre: Optional[float] = None,
    post: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "preSessionSUD": _clamp_sud(pre),
        "postSessionSUD": _clamp_sud(post),
    }


def _clamp_sud(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        return round(max(0.0, min(10.0, float(value))), 2)
    except (TypeError, ValueError):
        return None


def build_user_emotional_pattern(
    *,
    user_id: str,
    session_id: str = "",
    session_date: Optional[str] = None,
    physical_metrics: Optional[Dict[str, Any]] = None,
    cognitive_metrics: Optional[Dict[str, Any]] = None,
    sud_scores: Optional[Dict[str, Any]] = None,
    ai_intervention_effectiveness: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Canonical UserEmotionalPattern document (API / SQLite JSON mirror)."""
    eff = None
    if ai_intervention_effectiveness is not None:
        try:
            eff = int(max(1, min(5, round(float(ai_intervention_effectiveness)))))
        except (TypeError, ValueError):
            eff = None

    phys = physical_metrics or empty_physical_metrics()
    cogn = cognitive_metrics or empty_cognitive_metrics()
    sud = sud_scores or empty_sud_scores()

    # Normalize alternate key casings from clients
    if "cardSelectionDelay" not in phys and phys.get("card_selection_delay") is not None:
        phys["cardSelectionDelay"] = phys.get("card_selection_delay")
    if "gyroInstability" not in phys and phys.get("gyro_instability") is not None:
        phys["gyroInstability"] = phys.get("gyro_instability")
    if "cognitiveDistortionFlags" not in cogn and cogn.get("cognitive_distortion_flags"):
        cogn["cognitiveDistortionFlags"] = cogn["cognitive_distortion_flags"]
    if "coreWordFrequencies" not in cogn and cogn.get("core_word_frequencies"):
        cogn["coreWordFrequencies"] = cogn["core_word_frequencies"]
    if "preSessionSUD" not in sud and sud.get("pre_session_sud") is not None:
        sud["preSessionSUD"] = _clamp_sud(sud.get("pre_session_sud"))
    if "postSessionSUD" not in sud and sud.get("post_session_sud") is not None:
        sud["postSessionSUD"] = _clamp_sud(sud.get("post_session_sud"))

    doc = {
        "userId": user_id,
        "sessionId": session_id or "",
        "sessionDate": session_date or _utc_now(),
        "physicalMetrics": {
            "cardSelectionDelay": phys.get("cardSelectionDelay"),
            "gyroInstability": phys.get("gyroInstability"),
        },
        "cognitiveMetrics": {
            "cognitiveDistortionFlags": list(cogn.get("cognitiveDistortionFlags") or []),
            "coreWordFrequencies": list(cogn.get("coreWordFrequencies") or []),
            "defenseMechanismFlags": list(cogn.get("defenseMechanismFlags") or []),
            "modeAnalyzer": cogn.get("modeAnalyzer") or {},
        },
        "sudScores": {
            "preSessionSUD": _clamp_sud(sud.get("preSessionSUD")),
            "postSessionSUD": _clamp_sud(sud.get("postSessionSUD")),
        },
        "aiInterventionEffectiveness": eff,
        "extra": extra or {},
        "nonDiagnostic": True,
    }
    return doc


def extract_core_emotion_words(text: str, *, limit: int = 8) -> List[str]:
    corpus = text or ""
    hits: List[str] = []
    for word in EMOTION_CORE_WORDS:
        if word in corpus and word not in hits:
            hits.append(word)
        if len(hits) >= limit:
            break
    return hits


def infer_defense_mechanisms(
    text: str,
    *,
    mood_state: Optional[str] = None,
    distortions: Optional[Sequence[str]] = None,
) -> List[str]:
    t = (text or "").lower()
    flags: List[str] = []
    if mood_state == "DEFENSIVE" or any(k in t for k in ("괜찮", "별거", "그냥", "몰라", "피하", "회피")):
        flags.append("avoidance")
    if any(k in t for k in ("논리", "이유", "분석", "객관", "생각으로")):
        flags.append("intellectualization")
    if any(k in t for k in ("그 사람", "남들", "다들", "너 때문")):
        flags.append("projection")
    if any(k in t for k in ("아니야", "괜찮아", "아무렇", "안 아픈")):
        flags.append("denial")
    if any(k in t for k in ("어차피", "원래", "그게 맞아")):
        flags.append("rationalization")
    if mood_state == "VULNERABLE" and any(k in t for k in ("숨어", "혼자", "방에", "연락 끊")):
        flags.append("withdrawal")
    if "catastrophizing" in (distortions or []) and "avoidance" not in flags:
        flags.append("avoidance")
    # unique preserve order
    seen = set()
    out = []
    for f in flags:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def _distress_proxy(doc: Dict[str, Any]) -> Optional[float]:
    """0–10 distress proxy from SUD or cognitive intensity."""
    sud = doc.get("sudScores") or {}
    post = sud.get("postSessionSUD")
    pre = sud.get("preSessionSUD")
    if post is not None:
        return float(post)
    if pre is not None:
        return float(pre)
    cogn = doc.get("cognitiveMetrics") or {}
    n_dist = len(cogn.get("cognitiveDistortionFlags") or [])
    phys = doc.get("physicalMetrics") or {}
    gyro = phys.get("gyroInstability")
    delay = phys.get("cardSelectionDelay")
    score = 4.0 + n_dist * 0.9
    if isinstance(gyro, (int, float)):
        score += min(2.5, float(gyro) * 2.0)
    if isinstance(delay, (int, float)) and float(delay) > 8000:
        score += 0.8
    return round(min(10.0, max(0.0, score)), 2)


def save_emotional_pattern(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Upsert a UserEmotionalPattern row (keyed by userId + sessionId)."""
    ensure_emotional_pattern_table()
    user_id = doc["userId"]
    ensure_user(user_id)
    session_id = doc.get("sessionId") or f"anon-{_utc_now()}"
    session_date = doc.get("sessionDate") or _utc_now()
    phys = doc.get("physicalMetrics") or {}
    cogn = doc.get("cognitiveMetrics") or {}
    sud = doc.get("sudScores") or {}
    eff = doc.get("aiInterventionEffectiveness")

    conn = get_connection()
    try:
        # Merge with existing if present
        row = conn.execute(
            "SELECT pattern_json FROM user_emotional_patterns WHERE user_id = ? AND session_id = ?",
            (user_id, session_id),
        ).fetchone()
        if row:
            prev = json.loads(row["pattern_json"] or "{}")
            doc = _merge_pattern(prev, doc)
            phys = doc.get("physicalMetrics") or phys
            cogn = doc.get("cognitiveMetrics") or cogn
            sud = doc.get("sudScores") or sud
            eff = doc.get("aiInterventionEffectiveness")

        conn.execute(
            """
            INSERT INTO user_emotional_patterns (
                user_id, session_id, session_date,
                physical_metrics_json, cognitive_metrics_json, sud_scores_json,
                ai_intervention_effectiveness, pattern_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, session_id) DO UPDATE SET
                session_date = excluded.session_date,
                physical_metrics_json = excluded.physical_metrics_json,
                cognitive_metrics_json = excluded.cognitive_metrics_json,
                sud_scores_json = excluded.sud_scores_json,
                ai_intervention_effectiveness = excluded.ai_intervention_effectiveness,
                pattern_json = excluded.pattern_json
            """,
            (
                user_id,
                session_id,
                session_date,
                json.dumps(phys, ensure_ascii=False),
                json.dumps(cogn, ensure_ascii=False),
                json.dumps(sud, ensure_ascii=False),
                eff,
                json.dumps(doc, ensure_ascii=False),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    try:
        from app.services.psych_timeline import record_event

        record_event(
            user_id,
            "emotional_pattern_tick",
            {
                "session_id": session_id,
                "sudScores": sud,
                "cognitiveDistortionFlags": (cogn.get("cognitiveDistortionFlags") or [])[:8],
                "aiInterventionEffectiveness": eff,
                "non_diagnostic": True,
            },
            source_id=f"uep:{session_id}",
        )
    except Exception:
        pass

    return doc


def _merge_pattern(prev: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(prev)
    out.update({k: v for k, v in new.items() if k != "extra"})
    # Prefer non-null nested metrics
    for nest in ("physicalMetrics", "cognitiveMetrics", "sudScores"):
        merged = dict(prev.get(nest) or {})
        incoming = new.get(nest) or {}
        for k, v in incoming.items():
            if v is None:
                continue
            if isinstance(v, list):
                merged[k] = list(dict.fromkeys(list(merged.get(k) or []) + list(v)))
            else:
                merged[k] = v
        out[nest] = merged
    if new.get("aiInterventionEffectiveness") is not None:
        out["aiInterventionEffectiveness"] = new["aiInterventionEffectiveness"]
    extra = dict(prev.get("extra") or {})
    extra.update(new.get("extra") or {})
    out["extra"] = extra
    out["nonDiagnostic"] = True
    return out


def list_emotional_patterns(user_id: str, *, limit: int = 10) -> List[Dict[str, Any]]:
    ensure_emotional_pattern_table()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT pattern_json FROM user_emotional_patterns
            WHERE user_id = ?
            ORDER BY session_date DESC
            LIMIT ?
            """,
            (user_id, max(1, min(50, int(limit)))),
        ).fetchall()
    finally:
        conn.close()
    docs: List[Dict[str, Any]] = []
    for row in rows:
        try:
            docs.append(json.loads(row["pattern_json"] or "{}"))
        except json.JSONDecodeError:
            continue
    return docs


def analyze_personal_pattern(
    user_id: str,
    *,
    window: int = 8,
) -> Dict[str, Any]:
    """Time-series anomaly + cognitive/defense pattern report for one user.

    Uses the most recent 5–10 sessions (default 8). Output is prompt-ready and
    explicitly non-diagnostic.
    """
    window = max(5, min(10, int(window)))
    sessions = list_emotional_patterns(user_id, limit=window)
    if not sessions:
        return {
            "userId": user_id,
            "sampleSize": 0,
            "inEmotionalCrisisVsBaseline": False,
            "crisisConfidence": 0.0,
            "trend": "insufficient_data",
            "baselineDistress": None,
            "latestDistress": None,
            "topDistortions": [],
            "topDefenses": [],
            "patternReportKo": (
                "아직 이 유저의 누적 세션 패턴이 충분하지 않습니다. "
                "이번 대화에서는 보편적 공감·탐색부터 시작하세요."
            ),
            "promptHintKo": "",
            "nonDiagnostic": True,
        }

    distress_series = [_distress_proxy(s) for s in sessions]
    distress_series = [d for d in distress_series if d is not None]
    latest = distress_series[0] if distress_series else None
    baseline_vals = distress_series[1:] if len(distress_series) > 1 else distress_series[:]
    baseline = statistics.mean(baseline_vals) if baseline_vals else (latest or 5.0)
    std = statistics.pstdev(baseline_vals) if len(baseline_vals) >= 2 else 1.2

    anomaly = False
    confidence = 0.0
    if latest is not None:
        # Rising distress vs personal baseline (anomaly detection flavor)
        threshold = baseline + max(1.0, 1.15 * std)
        delta = latest - baseline
        anomaly = latest >= threshold or (delta >= 1.8 and latest >= 6.0)
        confidence = round(min(0.95, max(0.15, abs(delta) / 4.0 + (0.1 * len(sessions)))), 3)

    # Aggregate cognitive / defense / themes
    dist_hist: Dict[str, float] = {}
    def_hist: Dict[str, float] = {}
    word_hist: Dict[str, float] = {}
    for s in sessions:
        cogn = s.get("cognitiveMetrics") or {}
        for d in cogn.get("cognitiveDistortionFlags") or []:
            dist_hist[d] = dist_hist.get(d, 0) + 1.0
        for d in cogn.get("defenseMechanismFlags") or []:
            def_hist[d] = def_hist.get(d, 0) + 1.0
        for w in cogn.get("coreWordFrequencies") or []:
            word_hist[w] = word_hist.get(w, 0) + 1.0

    top_dist = sorted(dist_hist.items(), key=lambda x: -x[1])[:4]
    top_def = sorted(def_hist.items(), key=lambda x: -x[1])[:3]
    top_words = sorted(word_hist.items(), key=lambda x: -x[1])[:5]

    # Effectiveness trend
    eff_vals = [
        float(s["aiInterventionEffectiveness"])
        for s in sessions
        if s.get("aiInterventionEffectiveness") is not None
    ]
    avg_eff = round(statistics.mean(eff_vals), 2) if eff_vals else None

    # Theme hint from words (e.g. 이별-ish)
    theme_bits = []
    if any(w in ("서운", "그리움", "외로") for w, _ in top_words):
        theme_bits.append("관계·상실/거리감")
    if any(w in ("불안", "초조", "두려") for w, _ in top_words):
        theme_bits.append("불안·긴장")
    if any(w in ("우울", "무기력", "허무") for w, _ in top_words):
        theme_bits.append("우울·무기력")
    theme_clause = "·".join(theme_bits) if theme_bits else "일반 정서"

    dist_ko = [DISTORTION_LABELS_KO.get(k, k) for k, _ in top_dist]
    def_ko = [DEFENSE_LABELS_KO.get(k, k) for k, _ in top_def]

    if anomaly:
        crisis_line = (
            f"최근 {len(sessions)}회 중 최신 정서 부하({latest})가 "
            f"개인 베이스라인({baseline:.1f}) 대비 상승해, "
            f"우울·불안 쪽 위기 진입 신호가 있습니다(참고·비진단)."
        )
        trend = "elevated_vs_baseline"
    elif latest is not None and latest < baseline - 0.8:
        crisis_line = (
            f"최신 정서 부하({latest})는 베이스라인({baseline:.1f})보다 낮아, "
            f"상대적으로 안정 구간으로 보입니다(참고·비진단)."
        )
        trend = "improving"
    else:
        crisis_line = (
            f"최근 패턴은 개인 베이스라인({baseline:.1f}) 근처에서 움직입니다"
            f"(최신 {latest if latest is not None else 'N/A'})."
        )
        trend = "stable"

    if dist_ko:
        distort_line = (
            f"스트레스 상황에서 자주 관찰된 인지적 왜곡: "
            f"{', '.join(dist_ko)}. "
            f"특히 '{theme_clause}' 주제 근처에서 "
            f"'{dist_ko[0]}' 빈도가 높습니다."
        )
    else:
        distort_line = "아직 뚜렷한 인지왜곡 누적은 적습니다. 열린 탐색을 유지하세요."

    if def_ko:
        defense_line = f"주로 쓰는 방어 기제(휴리스틱): {', '.join(def_ko)}."
    else:
        defense_line = "방어 기제 신호는 아직 약합니다."

    report = " ".join([crisis_line, distort_line, defense_line])
    if avg_eff is not None:
        report += f" 최근 AI 인지재구성 수용도 평균은 {avg_eff}/5입니다."

    hint_parts = []
    if anomaly:
        hint_parts.append("지금은 해결책보다 로저스식 수용·안전감을 우선하세요.")
    if dist_ko:
        hint_parts.append(
            f"'{dist_ko[0]}'이 보이면 부드러운 소크라테스 질문으로만 재구성하세요."
        )
    if "avoidance" in [k for k, _ in top_def]:
        hint_parts.append("회피가 보이면 직면을 압박하지 말고 선택지를 작게 열어 주세요.")

    return {
        "userId": user_id,
        "sampleSize": len(sessions),
        "window": window,
        "inEmotionalCrisisVsBaseline": bool(anomaly),
        "crisisConfidence": confidence,
        "trend": trend,
        "baselineDistress": round(float(baseline), 2),
        "latestDistress": latest,
        "distressSeries": distress_series,
        "topDistortions": [
            {"id": k, "labelKo": DISTORTION_LABELS_KO.get(k, k), "count": int(v)}
            for k, v in top_dist
        ],
        "topDefenses": [
            {"id": k, "labelKo": DEFENSE_LABELS_KO.get(k, k), "count": int(v)}
            for k, v in top_def
        ],
        "topEmotionWords": [{"word": w, "count": int(c)} for w, c in top_words],
        "avgInterventionEffectiveness": avg_eff,
        "patternReportKo": report,
        "promptHintKo": " ".join(hint_parts),
        "nonDiagnostic": True,
    }


def personal_pattern_prompt_block(analysis: Optional[Dict[str, Any]]) -> str:
    """Inject analyze_personal_pattern() into 이서연 system context."""
    if not analysis or int(analysis.get("sampleSize") or 0) < 1:
        return ""
    lines = [
        "## [개인 고유 정서 패턴 — 참고용·비진단]",
        f"- 샘플 세션: {analysis.get('sampleSize')}회 (최근 창)",
        f"- 추세: {analysis.get('trend')} · "
        f"베이스라인 대비 위기진입={analysis.get('inEmotionalCrisisVsBaseline')} "
        f"(신뢰 {analysis.get('crisisConfidence')})",
        f"- 패턴 요약: {analysis.get('patternReportKo')}",
    ]
    hint = (analysis.get("promptHintKo") or "").strip()
    if hint:
        lines.append(f"- 맞춤 CBT 힌트: {hint}")
    tops = analysis.get("topDistortions") or []
    if tops:
        lines.append(
            "- 이 유저 고유 왜곡 우선순위: "
            + ", ".join(f"{t.get('labelKo')}×{t.get('count')}" for t in tops[:3])
        )
    lines.append(
        "- 위 정보는 진단이 아닙니다. 내담자 앞에서 수치·라벨을 그대로 말하지 말고, "
        "공감 후 그 패턴에 맞는 초점 질문 하나로만 맞춤 반응하세요."
    )
    return "\n".join(lines)


def record_pattern_from_chat_session(
    user_id: str,
    session: Any,
    *,
    pre_sud: Optional[float] = None,
    post_sud: Optional[float] = None,
    intervention_effectiveness: Optional[float] = None,
    physical_metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build + persist pattern snapshot after a counseling turn/session.

    Common core (physical + SUD + longitudinal flags) always runs.
    Mode-specific analyzers enrich cognitiveMetrics only.
    """
    from app.services.commercial_license_context import resolve_license_context
    from app.services.mode_analyzers import (
        merge_analyzer_into_cognitive_metrics,
        run_mode_specific_analyzer,
    )
    from app.services.persona_router import detect_cognitive_distortions

    messages = getattr(session, "messages", None) or []
    user_texts = [
        (m.get("content") or "")
        for m in messages
        if (m.get("role") == "user")
    ]
    corpus = "\n".join(user_texts[-8:])
    routing = getattr(session, "persona_routing", None) or {}
    distortions = list(routing.get("detected_distortions") or [])
    for d in detect_cognitive_distortions(corpus):
        if d not in distortions:
            distortions.append(d)

    mode = getattr(session, "consultation_mode", None) or "psychology"
    analyzer = run_mode_specific_analyzer(mode, corpus, base_distortions=distortions)
    distortions = list(analyzer.get("cognitiveDistortionFlags") or distortions)

    mood_state = routing.get("mood_state")
    defenses = infer_defense_mechanisms(corpus, mood_state=mood_state, distortions=distortions)
    words = extract_core_emotion_words(corpus)

    notes = getattr(session, "phase_notes", None) or {}
    stored = notes.get("emotional_pattern") or {}
    if pre_sud is None:
        pre_sud = stored.get("pre_sud")
    if post_sud is None:
        post_sud = stored.get("post_sud")
    if intervention_effectiveness is None:
        intervention_effectiveness = stored.get("intervention_effectiveness")

    if pre_sud is None:
        quant = getattr(session, "quant_features", None) or {}
        stress = quant.get("psychiatric_stress_weight")
        if isinstance(stress, (int, float)):
            pre_sud = round(float(stress) * 10.0, 2)
    if post_sud is None and pre_sud is not None:
        post_sud = max(0.0, float(pre_sud) - (0.4 if "rumination" not in distortions else 0.1))

    phys = physical_metrics or stored.get("physical_metrics") or empty_physical_metrics()
    tarot_phys = (notes.get("tarot_physical_metrics") or {}) if isinstance(notes, dict) else {}
    if tarot_phys:
        phys = {
            "cardSelectionDelay": tarot_phys.get("cardSelectionDelay", phys.get("cardSelectionDelay")),
            "gyroInstability": tarot_phys.get("gyroInstability", phys.get("gyroInstability")),
        }

    lic = resolve_license_context(user_id, session=session)
    cogn = merge_analyzer_into_cognitive_metrics(
        empty_cognitive_metrics(
            distortion_flags=distortions,
            core_words=words,
            defense_flags=defenses,
        ),
        analyzer,
    )

    doc = build_user_emotional_pattern(
        user_id=user_id,
        session_id=getattr(session, "session_id", "") or "",
        physical_metrics=phys,
        cognitive_metrics=cogn,
        sud_scores=empty_sud_scores(pre=pre_sud, post=post_sud),
        ai_intervention_effectiveness=intervention_effectiveness,
        extra={
            "counseling_phase": getattr(session, "counseling_phase", None),
            "persona_school": routing.get("school"),
            "turn_count": getattr(session, "turn_count", 0),
            "consultationMode": mode,
            "licenseType": lic.get("licenseType"),
            "organizationId": lic.get("organizationId"),
            "modeAnalyzerId": analyzer.get("analyzerId"),
        },
    )
    saved = save_emotional_pattern(doc)

    # B2B SOS (threshold) — shared core analysis + mode analyzer
    try:
        from app.services.b2b_sos import maybe_trigger_b2b_sos
        from app.services.emotional_pattern import analyze_personal_pattern

        analysis = analyze_personal_pattern(user_id)
        alert = maybe_trigger_b2b_sos(
            license_type=lic.get("licenseType") or "B2C_personal",
            org_id=lic.get("organizationId"),
            user_id=user_id,
            consultation_mode=mode,
            session_id=getattr(session, "session_id", "") or "",
            pattern_analysis=analysis,
            mode_analyzer=analyzer,
            latest_sud=post_sud if post_sud is not None else pre_sud,
            messages=messages,
        )
        if alert:
            saved["sos_alert"] = {
                "id": alert.get("id"),
                "alert_level": alert.get("alert_level"),
                "reason_codes": alert.get("reason_codes"),
                "delivery": alert.get("delivery"),
            }
            if isinstance(notes, dict):
                notes["last_sos_alert"] = saved["sos_alert"]
    except Exception:
        pass

    return saved


def record_tarot_physical_metrics(
    user_id: str,
    *,
    session_id: str = "",
    card_selection_delay_ms: Optional[float] = None,
    gyro_instability: Optional[float] = None,
    source_id: str = "",
) -> Dict[str, Any]:
    """Persist / merge physical metrics from tarot pick telemetry."""
    sid = session_id or source_id or f"tarot-{_utc_now()}"
    existing = None
    for doc in list_emotional_patterns(user_id, limit=5):
        if doc.get("sessionId") == sid:
            existing = doc
            break
    base = existing or build_user_emotional_pattern(user_id=user_id, session_id=sid)
    base["physicalMetrics"] = empty_physical_metrics(
        card_selection_delay_ms=card_selection_delay_ms
        if card_selection_delay_ms is not None
        else (base.get("physicalMetrics") or {}).get("cardSelectionDelay"),
        gyro_instability=gyro_instability
        if gyro_instability is not None
        else (base.get("physicalMetrics") or {}).get("gyroInstability"),
    )
    base["sessionId"] = sid
    return save_emotional_pattern(base)
