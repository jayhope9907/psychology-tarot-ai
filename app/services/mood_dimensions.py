from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

MOOD_DIMENSION_KEYS: Tuple[str, ...] = ("valence", "energy", "anxiety", "social", "sleep")

MOOD_DIMENSION_META: Dict[str, Dict[str, str]] = {
    "valence": {
        "label": "기분",
        "low": "우울·무거움",
        "high": "밝음·여유",
        "emoji": "🎭",
    },
    "energy": {
        "label": "에너지",
        "low": "무기력",
        "high": "활력",
        "emoji": "⚡",
    },
    "anxiety": {
        "label": "불안",
        "low": "차분",
        "high": "긴장·걱정",
        "emoji": "🌊",
    },
    "social": {
        "label": "관계",
        "low": "고립·거리",
        "high": "연결·교류",
        "emoji": "🤝",
    },
    "sleep": {
        "label": "수면",
        "low": "피로·불면",
        "high": "회복·휴식",
        "emoji": "🌙",
    },
}

AGENT_MODES: Dict[str, Dict[str, str]] = {
    "comfort": {
        "label": "위로·안전",
        "focus": "감정 인정, 안전감, 판단 없는 동행",
        "tone": "매우 부드럽고 느리게. 해결보다 지금의 pain을 함께 견디기.",
    },
    "calm": {
        "label": "진정·호흡",
        "focus": "불안 완화, 호흡·grounding, catastrophizing 완화",
        "tone": "차분하고 안정적으로. 몸과 호흡에 먼저 연결.",
    },
    "restore": {
        "label": "회복·에너지",
        "focus": "작은 성취, 무리하지 않기, 에너지 회복",
        "tone": "지지적이고 현실적으로. 큰 목표 대신 오늘 가능한 한 걸음.",
    },
    "connect": {
        "label": "관계·연결",
        "focus": "고립감 완화, 관계 욕구 탐색, 자기 돌봄",
        "tone": "따뜻하고 수용적으로. 혼자가 아님을 느끼게.",
    },
    "rest": {
        "label": "수면·리듬",
        "focus": "수면·피로, 일과 리듬, 몸의 신호",
        "tone": "부드럽고 차분하게. 쉼과 회복을 허용.",
    },
    "growth": {
        "label": "성장·탐색",
        "focus": "자기 이해, 패턴 탐색, 강점 확장",
        "tone": "밝고 지지적으로. 성장과 자기 이해 프레이밍.",
    },
    "balance": {
        "label": "균형·탐색",
        "focus": "감정 반영 + 한 걸음 더 깊은 질문",
        "tone": "균형 잡힌 공감. 탐색과 안내를 함께.",
    },
}


def clamp_dimension(value: int) -> int:
    return max(1, min(5, int(value)))


def normalize_dimensions(raw: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    source = raw or {}
    dims: Dict[str, int] = {}
    for key in MOOD_DIMENSION_KEYS:
        try:
            dims[key] = clamp_dimension(source.get(key, 3))
        except (TypeError, ValueError):
            dims[key] = 3
    return dims


def default_dimensions_from_score(score: int) -> Dict[str, int]:
    score = clamp_dimension(score)
    anxiety = clamp_dimension(6 - score)
    return {
        "valence": score,
        "energy": score,
        "anxiety": anxiety,
        "social": score,
        "sleep": score,
    }


def composite_mood_score(dimensions: Dict[str, int]) -> int:
    d = normalize_dimensions(dimensions)
    anxiety_inverted = 6 - d["anxiety"]
    raw = (
        d["valence"] * 0.35
        + d["energy"] * 0.2
        + anxiety_inverted * 0.2
        + d["social"] * 0.125
        + d["sleep"] * 0.125
    )
    return clamp_dimension(round(raw))


def dimensions_to_json(dimensions: Dict[str, int]) -> str:
    return json.dumps(normalize_dimensions(dimensions), ensure_ascii=False)


def dimensions_from_json(raw: Optional[str]) -> Dict[str, int]:
    if not raw:
        return normalize_dimensions({})
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and parsed:
            return normalize_dimensions(parsed)
    except (json.JSONDecodeError, TypeError):
        pass
    return normalize_dimensions({})


def dimension_summary(dimensions: Dict[str, int]) -> str:
    d = normalize_dimensions(dimensions)
    parts = []
    for key in MOOD_DIMENSION_KEYS:
        meta = MOOD_DIMENSION_META[key]
        parts.append(f"{meta['label']} {d[key]}/5")
    return " · ".join(parts)


def dominant_concerns(dimensions: Dict[str, int]) -> List[str]:
    d = normalize_dimensions(dimensions)
    concerns: List[tuple[int, str, str]] = []
    if d["valence"] <= 2:
        concerns.append((5 - d["valence"], "valence", "기분이 무겁게 느껴지는"))
    if d["anxiety"] >= 4:
        concerns.append((d["anxiety"], "anxiety", "불안·긴장이 높은"))
    if d["energy"] <= 2:
        concerns.append((5 - d["energy"], "energy", "에너지가 낮은"))
    if d["social"] <= 2:
        concerns.append((5 - d["social"], "social", "관계·연결에서 외로운"))
    if d["sleep"] <= 2:
        concerns.append((5 - d["sleep"], "sleep", "수면·피로가 쌓인"))
    concerns.sort(reverse=True)
    return [text for _, _, text in concerns[:3]]


def resolve_agent_mode(dimensions: Dict[str, int], composite_score: int) -> str:
    d = normalize_dimensions(dimensions)
    if d["valence"] <= 2 and d["anxiety"] >= 4:
        return "comfort"
    if d["anxiety"] >= 4:
        return "calm"
    if d["valence"] <= 2:
        return "comfort"
    if d["energy"] <= 2:
        return "restore"
    if d["social"] <= 2:
        return "connect"
    if d["sleep"] <= 2:
        return "rest"
    if composite_score >= 4 and d["energy"] >= 4:
        return "growth"
    if composite_score >= 4:
        return "growth"
    return "balance"


@dataclass
class MoodAgentProfile:
    mode: str
    label: str
    focus: str
    tone: str
    composite_score: int
    dimensions: Dict[str, int]
    concerns: List[str] = field(default_factory=list)
    sphere: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "label": self.label,
            "focus": self.focus,
            "tone": self.tone,
            "composite_score": self.composite_score,
            "dimensions": self.dimensions,
            "dimension_summary": dimension_summary(self.dimensions),
            "concerns": self.concerns,
            "sphere": self.sphere,
        }


def build_sphere_visual(dimensions: Dict[str, int]) -> Dict[str, float]:
    """3D UI hints: rotateX=energy, rotateY=valence, scale from anxiety, hue from valence."""
    d = normalize_dimensions(dimensions)
    return {
        "rotateX": round((d["energy"] - 3) * 12, 1),
        "rotateY": round((d["valence"] - 3) * 14, 1),
        "rotateZ": round((d["social"] - 3) * 8, 1),
        "scale": round(max(0.72, 1.08 - (d["anxiety"] - 1) * 0.07), 2),
        "glow": round(min(1.0, 0.35 + d["social"] * 0.12 + d["valence"] * 0.05), 2),
        "hue": round(max(0, min(360, 210 - (d["valence"] - 3) * 28 + (d["anxiety"] - 3) * 12)), 0),
        "pulse": round(max(0, (d["anxiety"] - 2) * 0.18), 2),
        "valence": d["valence"],
        "energy": d["energy"],
        "anxiety": d["anxiety"],
        "social": d["social"],
        "sleep": d["sleep"],
    }


def build_mood_agent_profile(
    dimensions: Optional[Dict[str, int]] = None,
    composite_score: Optional[int] = None,
) -> MoodAgentProfile:
    dims = normalize_dimensions(dimensions)
    composite = composite_score if composite_score is not None else composite_mood_score(dims)
    mode = resolve_agent_mode(dims, composite)
    agent = AGENT_MODES[mode]
    return MoodAgentProfile(
        mode=mode,
        label=agent["label"],
        focus=agent["focus"],
        tone=agent["tone"],
        composite_score=composite,
        dimensions=dims,
        concerns=dominant_concerns(dims),
        sphere=build_sphere_visual(dims),
    )


def build_agent_system_block(profile: MoodAgentProfile) -> str:
    lines = [
        "## [필수] 입체 기분 맞춤 AI 에이전트",
        f"- **에이전트 모드:** {profile.label} ({profile.mode})",
        f"- **맞춤 초점:** {profile.focus}",
        f"- **말투:** {profile.tone}",
        f"- **오늘 마음 좌표:** {dimension_summary(profile.dimensions)}",
    ]
    if profile.concerns:
        lines.append(f"- **우선 돌볼 영역:** {', '.join(profile.concerns)}")
    lines.append(
        "- 5축(기분·에너지·불안·관계·수면)을 **입체적으로** 반영해 대화하세요. "
        "한 축만 보지 말고 조합을 이해하세요."
    )
    return "\n".join(lines)


def build_agent_welcome(profile: MoodAgentProfile, note: str = "", has_checkin: bool = True) -> str:
    counselor = "이서연 상담사"
    if not has_checkin:
        return (
            f"안녕하세요, {counselor}예요.\n\n"
            "홈에서 **입체 마음 체크인**(기분·에너지·불안·관계·수면)을 해 주시면, "
            "그에 맞춘 AI 상담 에이전트로 더 정확히 돕고 싶어요.\n\n"
            "지금 가장 먼저 나누고 싶은 마음이 있다면 들려주세요."
        )

    note_line = f'\n메모: "{note}"\n' if note else "\n"
    concern_line = ""
    if profile.concerns:
        concern_line = f"{profile.concerns[0]} 상태로 느껴지시는군요. "

    return (
        f"안녕하세요, {counselor}예요.\n\n"
        f"오늘 입체 체크인을 보니 **{profile.label}** 모드로 맞춰 드릴게요.{note_line}"
        f"{concern_line}"
        f"({dimension_summary(profile.dimensions)})\n\n"
        "지금 마음 그대로, 편한 속도로 이야기해 주세요."
    )
