"""Freud / Jung psychodynamic tracking sidecar for tarot + chat replies.

OUTPUT FORMAT RULE: model prose first, then exactly one final line of JSON
(no markdown fence). We parse that line for product telemetry and strip it
from the user-facing bubble.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

ARCHETYPE_HINTS: List[Tuple[str, Tuple[str, ...]]] = [
    ("그림자", ("숨", "미워", "싫", "인정 못", "어두운", "수치")),
    ("페르소나", ("괜찮은 척", "겉", "사람들 앞", "역할", "체면", "잘 보여")),
    ("아니마", ("그리움", "사랑", "관계", "연인", "따뜻", "여린")),
    ("아니무스", ("결단", "이성", "판단", "단호", "논리", "주장")),
    ("자아", ("나답", "선택", "중심", "정체", "나를")),
    ("영웅", ("해내", "도전", "버티", "맞서", "용기")),
    ("현자", ("깨달", "의미", "배움", "지혜", "이해")),
    ("어린아이", ("아이", "순수", "의존", "어리", "보호")),
    ("어머니", ("돌봄", "엄마", "양육", "안아", "보살")),
    ("트리كس터", ("장난", "뒤집", "혼란", "모순", "웃음")),
]

DEFENSE_HINTS: List[Tuple[str, Tuple[str, ...]]] = [
    ("투사", ("그 사람", "남들", "다들", "너 때문", "세상 탓")),
    ("억압", ("생각 안", "잊고", "안 떠올", "일단 묻", "덮")),
    ("합리화", ("어차피", "원래", "그래서 맞아", "이유 있")),
    ("부인", ("아니야", "괜찮은데", "아무렇", "문제없")),
    ("주지화", ("논리", "분석", "객관적으로", "생각으로")),
    ("철회", ("혼자", "거리", "연락 끊", "피하", "빠져")),
    ("반동형성", ("오히려 밝게", "웃으면서", "오히려 친절")),
    ("승화", ("글 쓰", "운동", "일로", "창작")),
]

METRIC_KEYS = (
    "ego_id_conflict",
    "shadow_index",
    "persona_fatigue",
    "dominant_archetype",
    "defense_mechanism",
)

_JSON_LINE_RE = re.compile(
    r"\{[^{}]*\"ego_id_conflict\"[^{}]*\"shadow_index\"[^{}]*\"persona_fatigue\""
    r"[^{}]*\"dominant_archetype\"[^{}]*\"defense_mechanism\"[^{}]*\}\s*$",
    re.DOTALL,
)
_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


def build_psychodynamic_output_directive() -> str:
    """Exact OUTPUT FORMAT RULE bound into system prompts."""
    return (
        "[OUTPUT FORMAT RULE]\n"
        "당신은 타로 리딩과 함께 유저의 심리 상태를 프로이트/융 이론 기반으로 정밀 추적해야 합니다.\n"
        "답변의 가장 마지막 줄에 아래 형식의 JSON 데이터만 정확히 포함 시켜주세요. "
        "앞뒤로 다른 텍스트나 마크다운(`json)을 붙이지 마세요.\n\n"
        '{"ego_id_conflict": 0~100, "shadow_index": 0~100, "persona_fatigue": 0~100, '
        '"dominant_archetype": "string", "defense_mechanism": "string"}\n\n'
        "- ego_id_conflict: 본능(이드)과 도덕적 억압(슈퍼에고) 사이의 갈등 수치\n"
        "- shadow_index: 유저가 외면하려는 그림자의 노출 및 거부 정도\n"
        "- persona_fatigue: 사회적 가면(페르소나)으로 인한 피로도\n"
        "- dominant_archetype: 현재 대화에서 강하게 나타나는 융의 원형 "
        "(예: 자아, 그림자, 페르소나, 아니마 등)\n"
        "- defense_mechanism: 유저가 주로 사용 중인 방어기제 "
        "(예: 투사, 억압, 합리화 등)\n"
        "중요: 위 JSON은 **마지막 한 줄**만. 진단명·병명 단정 금지. 참고용 웰니스 지표.\n"
    )


def _clamp_score(value: Any, default: int = 40) -> int:
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        n = default
    return max(0, min(100, n))


def normalize_psychodynamic_metrics(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    data = raw or {}
    return {
        "ego_id_conflict": _clamp_score(data.get("ego_id_conflict"), 45),
        "shadow_index": _clamp_score(data.get("shadow_index"), 40),
        "persona_fatigue": _clamp_score(data.get("persona_fatigue"), 40),
        "dominant_archetype": str(data.get("dominant_archetype") or "자아").strip()[:40] or "자아",
        "defense_mechanism": str(data.get("defense_mechanism") or "억압").strip()[:40] or "억압",
        "non_diagnostic": True,
    }


def metrics_to_json_line(metrics: Dict[str, Any]) -> str:
    clean = normalize_psychodynamic_metrics(metrics)
    return json.dumps(
        {
            "ego_id_conflict": clean["ego_id_conflict"],
            "shadow_index": clean["shadow_index"],
            "persona_fatigue": clean["persona_fatigue"],
            "dominant_archetype": clean["dominant_archetype"],
            "defense_mechanism": clean["defense_mechanism"],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def estimate_psychodynamic_metrics(
    user_text: str,
    *,
    assistant_text: str = "",
) -> Dict[str, Any]:
    """Heuristic fallback when the model omits the trailing JSON line."""
    corpus = f"{user_text}\n{assistant_text}".lower()
    conflict = 35
    shadow = 30
    fatigue = 30
    if any(k in corpus for k in ("죄책", "해야할", "참아", "도덕", "창피", "욕망")):
        conflict += 25
    if any(k in corpus for k in ("숨", "인정 못", "미워", "싫어하는 나", "어두운")):
        shadow += 28
    if any(k in corpus for k in ("괜찮은 척", "사람들 앞", "지쳐", "역할", "체면")):
        fatigue += 28
    if any(k in corpus for k in ("불안", "우울", "힘들", "무너")):
        conflict += 10
        shadow += 8
        fatigue += 8

    archetype = "자아"
    best = 0
    for name, keys in ARCHETYPE_HINTS:
        hits = sum(1 for k in keys if k in corpus)
        if hits > best:
            best = hits
            archetype = name

    defense = "억압"
    best_d = 0
    for name, keys in DEFENSE_HINTS:
        hits = sum(1 for k in keys if k in corpus)
        if hits > best_d:
            best_d = hits
            defense = name

    return normalize_psychodynamic_metrics(
        {
            "ego_id_conflict": conflict,
            "shadow_index": shadow,
            "persona_fatigue": fatigue,
            "dominant_archetype": archetype,
            "defense_mechanism": defense,
        }
    )


def extract_psychodynamic_metrics(text: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Split display prose from trailing metrics JSON.

    Returns (display_text, metrics_or_None).
    """
    raw = (text or "").strip()
    if not raw:
        return "", None

    # Prefer fenced block if model violates the rule
    fence = _FENCE_RE.search(raw)
    if fence:
        try:
            metrics = normalize_psychodynamic_metrics(json.loads(fence.group(1)))
            display = (raw[: fence.start()] + raw[fence.end() :]).strip()
            return display, metrics
        except json.JSONDecodeError:
            pass

    lines = raw.splitlines()
    # Search last non-empty lines for JSON object
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if not line:
            continue
        if line.startswith("```"):
            continue
        candidate = line
        if not candidate.startswith("{"):
            # sometimes prefixed with label
            brace = candidate.find("{")
            if brace >= 0:
                candidate = candidate[brace:]
        if "ego_id_conflict" not in candidate:
            break
        try:
            metrics = normalize_psychodynamic_metrics(json.loads(candidate))
            display = "\n".join(lines[:i]).rstrip()
            return display, metrics
        except json.JSONDecodeError:
            # try broader match
            m = _JSON_LINE_RE.search(candidate)
            if m:
                try:
                    metrics = normalize_psychodynamic_metrics(json.loads(m.group(0)))
                    display = "\n".join(lines[:i]).rstrip()
                    return display, metrics
                except json.JSONDecodeError:
                    pass
            break

    return raw, None


def ensure_psychodynamic_metrics(
    text: str,
    *,
    user_text: str = "",
) -> Tuple[str, Dict[str, Any]]:
    """Parse trailing JSON or synthesize + do not re-append JSON to display text."""
    display, metrics = extract_psychodynamic_metrics(text)
    if metrics is None:
        metrics = estimate_psychodynamic_metrics(user_text, assistant_text=display)
    return display, metrics
