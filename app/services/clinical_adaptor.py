from __future__ import annotations

from typing import Any, Dict


VALID_RESISTANCE = {"LOW", "MEDIUM", "HIGH"}
VALID_COGNITIVE = {"STANDARD", "SIMPLE_EASY"}


def normalize_resistance_level(raw: Any) -> str:
    text = str(raw or "").strip().upper()
    return text if text in VALID_RESISTANCE else "LOW"


def normalize_cognitive_level(raw: Any) -> str:
    text = str(raw or "").strip().upper()
    return text if text in VALID_COGNITIVE else "STANDARD"


def normalize_clinical_setup(
    *,
    resistance_level: Any = None,
    sensory_impairment_deaf: Any = None,
    cognitive_level: Any = None,
) -> Dict[str, Any]:
    resistance = normalize_resistance_level(resistance_level)
    cognitive = normalize_cognitive_level(cognitive_level)
    deaf = bool(sensory_impairment_deaf)
    return {
        "resistance_level": resistance,
        "sensory_impairment_deaf": deaf,
        "cognitive_level": cognitive,
        "adaptive_enabled": (resistance == "HIGH" or deaf or cognitive == "SIMPLE_EASY"),
    }


def build_clinical_adaptor_prompt(setup: Dict[str, Any]) -> str:
    """Adaptive Clinical Setup prompt rules for clinical-vulnerable clients."""
    resistance = normalize_resistance_level(setup.get("resistance_level"))
    deaf = bool(setup.get("sensory_impairment_deaf"))
    cognitive = normalize_cognitive_level(setup.get("cognitive_level"))
    enabled = bool(setup.get("adaptive_enabled"))

    if not enabled:
        return ""

    lines = [
        "## Adaptive Clinical Setup (B2B 임상 취약 내담자 보정 필터)",
        f"- resistance_level={resistance}, sensory_impairment_deaf={str(deaf).lower()}, cognitive_level={cognitive}",
        "- 답변은 짧고 쉬운 문장(초등 저학년 수준 어휘)을 사용하세요.",
        "- 검사/테스트/진단/스크리닝 같은 단어를 그대로 쓰지 말고 '마음 확인', '가벼운 체크'로 순화하세요.",
    ]
    if deaf:
        lines.extend(
            [
                "- 청각 의존 표현(들리나요/말해볼까요/소리로)은 피하고, 시각 중심 표현을 사용하세요.",
                "- 핵심 내용 마지막에 이모지 요약 1줄을 붙이세요. (예: 🙂 안정, 🌬️ 호흡, ✍️ 한 줄 기록)",
            ]
        )
    else:
        lines.append("- 필요 시 마지막에 이모지 요약 1줄을 붙이세요. (예: 🙂 안정, 🌬️ 호흡, ✍️ 한 줄 기록)")

    if resistance == "HIGH":
        lines.append("- '왜 해야 하죠?' 저항을 낮추기 위해 선택권을 먼저 제시하고 강요하지 마세요.")

    if cognitive == "SIMPLE_EASY":
        lines.append("- 한번에 1가지 행동만 제안하고, 문장당 핵심 1개만 전달하세요.")

    lines.append("- 위 규칙은 임상 전달 보정용이며, 진단 단정은 금지합니다.")
    return "\n".join(lines)

