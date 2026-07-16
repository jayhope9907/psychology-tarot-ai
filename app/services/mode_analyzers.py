"""Mode-specific analyzers + shared emotional-pattern core bridge (patent layer).

Common core (gyro / pick delay / SUD / longitudinal EMA) lives in
`emotional_pattern` and is NEVER branched by consultationMode.
This module only adds mode-specialized cognitive / spiritual detectors.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from app.services.consultation_mode import (
    MODE_FAITH,
    MODE_PSYCHOLOGY,
    SPIRITUAL_DISTORTION_LABELS_KO,
    detect_spiritual_distortions,
    normalize_consultation_mode,
)

# ── psychology: classic 15 CBT cognitive distortions ─────────────────
CBT_15_KEYWORDS: Dict[str, Sequence[str]] = {
    "all_or_nothing": ("완전", "전부", "항상", "절대", "흑백", "0아니면"),
    "overgeneralization": ("늘", "매번", "역시", "또", "모두", "다들"),
    "mental_filter": ("이것만", "나쁜 것만", "부정적인 면만", "한 가지뿐"),
    "disqualifying_positive": ("그래도 의미 없", "그거 아니고", "운일 뿐", "별로야"),
    "mind_reading": ("분명 생각", "나를 무시", "싫어할 게", "욕할 게"),
    "fortune_telling": ("망할 거", "안 될 거", "실패할 게", "금방 끝"),
    "magnification": ("최악", "큰일", "파국", "끝장", "재앙"),
    "emotional_reasoning": ("느끼니까", "기분상", "감정적으로", "느낌이"),
    "should_statements": ("해야 해", "해야만", "하면 안", "당연히", "의무"),
    "labeling": ("나는 루저", "찌질", "쓰레기", "형편없", "실패자"),
    "personalization": ("내 탓", "내 때문", "내가 망", "다 나 때문"),
    "blaming": ("너 때문", "그 사람 탓", "세상 탓", "남 탓"),
    "control_fallacy": ("어쩔 수 없", "통제 못", "내가 다 맞춰", "마음대로 안"),
    "fallacy_of_fairness": ("불공평", "왜 나만", "공정하지", "너무 부당"),
    "always_being_right": ("내가 맞아", "틀릴 리 없", "절대 안 틀", "네 말이 틀"),
}

CBT_15_LABELS_KO: Dict[str, str] = {
    "all_or_nothing": "흑백논리",
    "overgeneralization": "과잉일반화",
    "mental_filter": "정신적 여과",
    "disqualifying_positive": "긍정 평가절하",
    "mind_reading": "독심술",
    "fortune_telling": "예언적 사고",
    "magnification": "확대·파국화",
    "emotional_reasoning": "감정적 추론",
    "should_statements": "당위적 사고",
    "labeling": "낙인찍기",
    "personalization": "개인화",
    "blaming": "비난",
    "control_fallacy": "통제 오류",
    "fallacy_of_fairness": "공정성 오류",
    "always_being_right": "무조건 옳음",
}

# ── faith: spiritual dryness (영적 탈진) ──────────────────────────────
SPIRITUAL_DRYNESS_KEYWORDS: Sequence[str] = (
    "영적 탈진",
    "영적 메마",
    "메마름",
    "기도와 멀",
    "기도가 안",
    "예배가 형식",
    "무감동",
    "하나님 침묵",
    "영적 공허",
    "믿음이 식",
    "신앙 번아웃",
    "예배 가기 싫",
    "묵상이 안",
    "영혼이 건조",
    "은혜가 안",
)


def detect_cbt_15_distortions(text: str) -> List[str]:
    corpus = (text or "").lower()
    hits: List[str] = []
    for code, keywords in CBT_15_KEYWORDS.items():
        if any(k in corpus for k in keywords):
            hits.append(code)
    return hits


def detect_spiritual_dryness(text: str) -> Dict[str, Any]:
    corpus = text or ""
    matched = [k for k in SPIRITUAL_DRYNESS_KEYWORDS if k in corpus]
    score = min(1.0, 0.22 * len(matched) + (0.15 if "탈진" in corpus or "번아웃" in corpus else 0.0))
    return {
        "detected": bool(matched),
        "score": round(score, 3),
        "matched_keywords": matched[:6],
        "labelKo": "영적 탈진(Spiritual Dryness)",
    }


def run_mode_specific_analyzer(
    mode: str,
    text: str,
    *,
    base_distortions: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Branching analyzer: psychology → CBT-15, faith → spiritual distortions + dryness."""
    mode_n = normalize_consultation_mode(mode)
    base = list(base_distortions or [])

    if mode_n == MODE_FAITH:
        spiritual = detect_spiritual_distortions(text)
        dryness = detect_spiritual_dryness(text)
        merged = list(dict.fromkeys(base + spiritual))
        return {
            "consultationMode": MODE_FAITH,
            "analyzerId": "faith_spiritual_cognition_v1",
            "cognitiveDistortionFlags": merged,
            "spiritualDistortionFlags": spiritual,
            "spiritualDistortionLabelsKo": [
                SPIRITUAL_DISTORTION_LABELS_KO.get(x, x) for x in spiritual
            ],
            "spiritualDryness": dryness,
            "cbt15Flags": [],
            "promptHintKo": (
                "영적 탈진·정죄 루프가 보이면 먼저 안식과 임재의 감각을 지키고, "
                "묵상은 강요하지 마세요."
                if dryness.get("detected") or spiritual
                else "신앙 언어를 존중하며 공감으로 머무르세요."
            ),
        }

    cbt = detect_cbt_15_distortions(text)
    merged = list(dict.fromkeys(base + cbt))
    return {
        "consultationMode": MODE_PSYCHOLOGY,
        "analyzerId": "psychology_cbt15_v1",
        "cognitiveDistortionFlags": merged,
        "cbt15Flags": cbt,
        "cbt15LabelsKo": [CBT_15_LABELS_KO.get(x, x) for x in cbt],
        "spiritualDistortionFlags": [],
        "spiritualDryness": {"detected": False, "score": 0.0, "matched_keywords": []},
        "promptHintKo": (
            f"CBT 15대 왜곡 중 {[CBT_15_LABELS_KO.get(x, x) for x in cbt[:3]]} 신호가 있습니다. "
            "부드러운 소크라테스 질문으로만 재구성하세요."
            if cbt
            else "열린 CBT 탐색을 유지하세요."
        ),
    }


def merge_analyzer_into_cognitive_metrics(
    cognitive_metrics: Dict[str, Any],
    analyzer: Dict[str, Any],
) -> Dict[str, Any]:
    """Attach mode flags into shared cognitiveMetrics JSON (core store stays unified)."""
    out = dict(cognitive_metrics or {})
    flags = list(out.get("cognitiveDistortionFlags") or [])
    for f in analyzer.get("cognitiveDistortionFlags") or []:
        if f not in flags:
            flags.append(f)
    out["cognitiveDistortionFlags"] = flags
    out["modeAnalyzer"] = {
        "analyzerId": analyzer.get("analyzerId"),
        "consultationMode": analyzer.get("consultationMode"),
        "cbt15Flags": analyzer.get("cbt15Flags") or [],
        "spiritualDistortionFlags": analyzer.get("spiritualDistortionFlags") or [],
        "spiritualDryness": analyzer.get("spiritualDryness") or {},
    }
    return out
