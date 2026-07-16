"""Consultation mode switching: psychology | faith.

Persona/prompt layers switch by mode. Physical telemetry (gyro / card delay)
and the personal emotional-pattern *core* stay mode-agnostic — only how
results are narrated into the system prompt changes.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from app.services.persistence import get_user_settings, save_user_settings

MODE_PSYCHOLOGY = "psychology"
MODE_FAITH = "faith"
VALID_MODES = (MODE_PSYCHOLOGY, MODE_FAITH)

SETTINGS_KEY = "consultationMode"  # camelCase per product schema
SETTINGS_KEY_ALT = "consultation_mode"

# Spiritual / pastoral cognitive distortion heuristics (faith mode)
SPIRITUAL_DISTORTION_KEYWORDS: Dict[str, Sequence[str]] = {
    "divine_punishment": ("벌", "심판", "저주", "하나님이 미워", "하늘이 벌"),
    "condemnation_loop": ("정죄", "용서 못", "구원 없", "버림받", "영원한 죄"),
    "works_righteousness": ("착해야", "충분히 믿지", "기도 더", "예배 더", "헌신 부족"),
    "spiritual_all_or_nothing": ("완전 불신", "진짜 크리스천", "가짜 믿음", "전부 죄인"),
    "abandoned_by_god": ("하나님이 안", "응답 없", "침묵하", "떠나셨", "안 들으"),
    "prayer_transaction": ("이루어지지 않", "안 들어주", "거래", "조건부 사랑"),
}

SPIRITUAL_DISTORTION_LABELS_KO: Dict[str, str] = {
    "divine_punishment": "신벌·심판 과도귀인",
    "condemnation_loop": "정죄 루프",
    "works_righteousness": "행위 의로움 압박",
    "spiritual_all_or_nothing": "영적 흑백사고",
    "abandoned_by_god": "하나님 유기 감각",
    "prayer_transaction": "기도-거래 사고",
}


def normalize_consultation_mode(raw: Any) -> str:
    text = str(raw or "").strip().lower()
    if text in {"faith", "christian", "christianity", "pastoral", "spiritual", "신앙", "기독교"}:
        return MODE_FAITH
    return MODE_PSYCHOLOGY


def resolve_consultation_mode(
    user_id: str,
    *,
    session_mode: Optional[str] = None,
    override: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None,
) -> str:
    """Priority: explicit override → session → user settings → psychology."""
    if override:
        return normalize_consultation_mode(override)
    if session_mode:
        return normalize_consultation_mode(session_mode)
    cfg = settings if settings is not None else get_user_settings(user_id)
    stored = cfg.get(SETTINGS_KEY)
    if stored is None:
        stored = cfg.get(SETTINGS_KEY_ALT)
    return normalize_consultation_mode(stored)


def save_consultation_mode(user_id: str, mode: str) -> Dict[str, Any]:
    mode_n = normalize_consultation_mode(mode)
    settings = get_user_settings(user_id)
    settings[SETTINGS_KEY] = mode_n
    settings[SETTINGS_KEY_ALT] = mode_n  # dual-write for compatibility
    save_user_settings(user_id, settings)
    return {"user_id": user_id, "consultationMode": mode_n}


def detect_spiritual_distortions(text: str) -> List[str]:
    corpus = (text or "").lower()
    hits: List[str] = []
    for code, keywords in SPIRITUAL_DISTORTION_KEYWORDS.items():
        if any(k in corpus for k in keywords):
            hits.append(code)
    return hits


def enrich_distortions_for_mode(
    mode: str,
    base_distortions: Optional[Sequence[str]],
    user_text: str,
) -> List[str]:
    """Union of CBT flags (always) + spiritual flags when faith mode."""
    out: List[str] = list(base_distortions or [])
    if normalize_consultation_mode(mode) == MODE_FAITH:
        for d in detect_spiritual_distortions(user_text):
            if d not in out:
                out.append(d)
    return out


def build_psychology_mode_directive(counselor_name: str = "이서연") -> str:
    return (
        f"## 상담 모드: psychology (일반 심리상담)\n"
        f"당신은 {counselor_name} 상담사입니다. "
        "인간중심·CBT·필요 시 통합적 심리학 렌즈로 동행하세요.\n"
        "- 인지적 왜곡(흑백논리·파국화·감정적 추론 등)을 "
        "부드러운 소크라테스 질문으로 재구성하세요.\n"
        "- 진단·설교·종교 권유 금지. 비의료 웰니스 경계 유지.\n"
        "- 상징·타로가 있으면 투사·은유로만 다루세요.\n"
    )


def build_faith_mode_directive(counselor_name: str = "이서연") -> str:
    return (
        f"## 상담 모드: faith (기독교·묵상 상담)\n"
        f"당신은 {counselor_name}이며, **내담자가 선택한 신앙 동반 모드**에서 "
        "목회상담·기독교 상담의 온기로 곁에 머뭅니다.\n"
        "- 성경 구절·묵상 질문은 **강요하지 말고**, 내담자 언어에 맞춰 "
        "아주 작게만 초대하세요 (예: 「그 마음에 머무를 짧은 한 줄이 있을까요?」).\n"
        "- **영적 인지 왜곡**을 주의하세요: 신벌 과도귀인, 정죄 루프, "
        "행위 의로움 압박, 영적 흑백사고, 하나님 유기 감각, 기도-거래 사고.\n"
        "- 왜곡이 보이면 정죄하지 말고, 은혜·관계·정직한 감정 표현으로 "
        "생각을 부드럽게 열어 주세요 (영적 Soft Reframing).\n"
        "- 개종 강요·교파 논쟁·기적 단정·의료 대체 신유 주장 금지.\n"
        "- 위기(자해·자살) 시에는 신앙 위로만으로 끝내지 말고 "
        "1393·119·129 등 전문 자원을 또렷이 안내하세요.\n"
        "- 심리학 기법은 버리되, 공감·경청은 로저스와 같이 유지하세요.\n"
    )


def build_mode_system_directive(mode: str, *, counselor_name: str = "이서연") -> str:
    if normalize_consultation_mode(mode) == MODE_FAITH:
        return build_faith_mode_directive(counselor_name)
    return build_psychology_mode_directive(counselor_name)


def personal_pattern_prompt_for_mode(
    analysis: Optional[Dict[str, Any]],
    mode: str,
) -> str:
    """Mode-specific *narration* of the shared pattern-core analysis."""
    if not analysis or int(analysis.get("sampleSize") or 0) < 1:
        return ""

    mode_n = normalize_consultation_mode(mode)
    report = analysis.get("patternReportKo") or ""
    tops = analysis.get("topDistortions") or []

    if mode_n == MODE_FAITH:
        # Relabel known spiritual codes if present in series
        spiritual_hits = [
            t for t in tops if str(t.get("id") or "").startswith(
                ("divine_", "condemnation", "works_", "spiritual_", "abandoned_", "prayer_")
            )
            or t.get("id") in SPIRITUAL_DISTORTION_LABELS_KO
        ]
        lines = [
            "## [개인 정서 패턴 · faith 모드 해석 — 참고·비진단]",
            f"- 샘플 세션: {analysis.get('sampleSize')}회 · 추세 {analysis.get('trend')}",
            f"- 코어 요약(공용 알고리즘): {report}",
        ]
        if spiritual_hits or tops:
            mapped = []
            for t in (spiritual_hits or tops)[:4]:
                code = t.get("id")
                label = SPIRITUAL_DISTORTION_LABELS_KO.get(code) or t.get("labelKo") or code
                mapped.append(f"{label}×{t.get('count')}")
            lines.append("- 영적·인지 패턴 우선순위: " + ", ".join(mapped))
        if analysis.get("inEmotionalCrisisVsBaseline"):
            lines.append(
                "- 베이스라인 대비 정서 부하가 높습니다. "
                "먼저 안전·임재의 감각을 지키고, 묵상 초대는 최소화하세요."
            )
        lines.append(
            "- 수치·라벨을 내담자에게 그대로 말하지 말고, "
            "은혜와 정직한 감정으로 초점 질문 하나만 이어가세요."
        )
        return "\n".join(lines)

    # psychology default narration (delegate-compatible)
    from app.services.emotional_pattern import personal_pattern_prompt_block

    return personal_pattern_prompt_block(analysis)


def bind_consultation_mode_prompts(
    *,
    mode: str,
    counselor_name: str,
    pattern_analysis: Optional[Dict[str, Any]] = None,
    spiritual_distortions: Optional[Sequence[str]] = None,
) -> str:
    """Conditional prompt interface for mode switching."""
    parts = [build_mode_system_directive(mode, counselor_name=counselor_name)]
    pattern_block = personal_pattern_prompt_for_mode(pattern_analysis, mode)
    if pattern_block:
        parts.append(pattern_block)
    if normalize_consultation_mode(mode) == MODE_FAITH and spiritual_distortions:
        labels = [
            SPIRITUAL_DISTORTION_LABELS_KO.get(d, d) for d in spiritual_distortions
        ]
        parts.append(
            "## 이번 말에서 감지된 영적 인지 왜곡(휴리스틱)\n"
            "- " + ", ".join(labels) + "\n"
            "- 정죄하지 말고, 감정을 먼저 받든 뒤 은혜·관계의 여지를 작게 여세요."
        )
    return "\n\n".join(parts)


def mode_meta(mode: str) -> Dict[str, Any]:
    mode_n = normalize_consultation_mode(mode)
    return {
        "consultationMode": mode_n,
        "labelKo": "신앙·묵상 상담" if mode_n == MODE_FAITH else "심리상담",
        "sharedCores": ["gyro_physical_metrics", "emotional_pattern_core"],
        "promptStack": (
            ["faith_persona", "spiritual_distortion", "meditation_invite"]
            if mode_n == MODE_FAITH
            else ["psychology_persona", "cbt_reframing", "rogers_jung_cbt_triad"]
        ),
    }
