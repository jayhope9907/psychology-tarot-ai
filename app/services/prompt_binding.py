from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models.clinical import ClinicalSchool
from app.services.counseling_theories import build_theory_system_prompt, get_theory_meta
from app.services.persona_router import detect_cognitive_distortions


class PromptContextWeightBindingFactory:
    def __init__(
        self,
        school: ClinicalSchool,
        psychological_readiness_index: Optional[float] = None,
        cognitive_distortions: Optional[List[str]] = None,
        attachment_matrix_score: Optional[float] = None,
        tree_energy_index: Optional[float] = None,
        psychiatric_stress_weight: Optional[float] = None,
        structural_sign: Optional[str] = None,
    ):
        self.school = school or ClinicalSchool.INTEGRATIVE
        self.psychological_readiness_index = float(psychological_readiness_index or 0.5)
        self.cognitive_distortions = cognitive_distortions or []
        self.attachment_matrix_score = float(attachment_matrix_score if attachment_matrix_score is not None else 0.5)
        self.tree_energy_index = float(tree_energy_index if tree_energy_index is not None else 3.0)
        self.psychiatric_stress_weight = float(psychiatric_stress_weight if psychiatric_stress_weight is not None else 0.5)
        self.structural_sign = structural_sign or "stable"

    def _clamp(self, value: float) -> float:
        return round(min(1.0, max(0.0, value)), 2)

    def _severity_multiplier(self) -> float:
        stress = self._clamp(self.psychiatric_stress_weight)
        attachment_instability = self._clamp(1.0 - self.attachment_matrix_score)
        energy_load = self._clamp(self.tree_energy_index / 9.9)
        readiness_gap = self._clamp(1.0 - self.psychological_readiness_index)
        return self._clamp(0.35 + stress * 0.25 + attachment_instability * 0.2 + energy_load * 0.1 + readiness_gap * 0.1)

    def _context_block(self, severity: float) -> str:
        distortion_text = ", ".join(self.cognitive_distortions) if self.cognitive_distortions else "none"
        intensity = "낮음" if severity < 0.45 else "중간" if severity < 0.7 else "높음"
        return (
            "## 정형 퀀트 피처 컨텍스트\n"
            f"- psychological_readiness_index: {self.psychological_readiness_index:.2f}\n"
            f"- attachment_matrix_score: {self.attachment_matrix_score:.2f}\n"
            f"- tree_energy_index: {self.tree_energy_index:.2f}\n"
            f"- psychiatric_stress_weight: {self.psychiatric_stress_weight:.2f}\n"
            f"- structural_sign: {self.structural_sign}\n"
            f"- detected_cognitive_distortions: {distortion_text}\n"
            f"- clinical_intensity: {intensity} (severity_multiplier={severity:.2f})\n"
            "위 지표 심각도에 비례해 개입 강도를 조절하되, 진단명은 단정하지 마세요."
        )

    def build(self) -> Dict[str, Any]:
        readiness = self._clamp(self.psychological_readiness_index)
        distortion_count = max(0, len(self.cognitive_distortions))
        severity = self._severity_multiplier()
        meta = get_theory_meta(self.school)
        profile = meta["weight_profile"]

        interpretation_depth = self._clamp(profile["interpretation"] + severity * 0.15 + distortion_count * 0.03)
        empathy_level = self._clamp(profile["empathy"] + readiness * 0.1)
        homework_structure = self._clamp(profile["structure"] + severity * 0.12 + distortion_count * 0.04)
        confrontation_level = self._clamp(profile.get("confrontation", 0.25) + severity * 0.2)

        system_prompt = build_theory_system_prompt(
            self.school,
            severity,
            [d for d in self.cognitive_distortions if isinstance(d, str)],
        )
        weights = {
            "interpretation_depth": interpretation_depth,
            "empathy_level": empathy_level,
            "homework_structure": homework_structure,
            "confrontation_level": confrontation_level,
            "severity_multiplier": severity,
            "theory": self.school.value,
        }

        return {
            "weights": weights,
            "system_prompt": system_prompt,
            "context_block": self._context_block(severity),
            "severity_multiplier": severity,
        }


def extract_chat_quant_features(user_message: str, state: Any) -> Dict[str, Any]:
    normalized = (user_message or "").lower()
    readiness = 0.5
    if any(keyword in normalized for keyword in ("불안", "우울", "스트레스", "무기력", "상실", "두려움")):
        readiness -= 0.18
    if any(keyword in normalized for keyword in ("안정", "회복", "괜찮", "희망", "편안")):
        readiness += 0.15

    tree_energy = min(9.9, max(1.0, 2.5 + len(normalized.split()) * 0.16))
    stress_weight = min(0.95, 0.35 + (0.1 * len(detect_cognitive_distortions(normalized))))
    attachment = 0.5
    if any(keyword in normalized for keyword in ("관계", "사랑", "외로", "버림")):
        attachment = 0.38
    if any(keyword in normalized for keyword in ("안정", "믿", "지지")):
        attachment = 0.62

    structural_sign = "tension" if readiness < 0.45 else "calm" if readiness > 0.62 else "stable"
    distortions = detect_cognitive_distortions(user_message)
    for entry in state.messages[-4:]:
        if entry.get("role") == "user":
            distortions.extend(detect_cognitive_distortions(entry.get("content", "")))
    distortions = list(dict.fromkeys(distortions))

    return {
        "psychological_readiness_index": round(max(0.0, min(1.0, readiness)), 2),
        "tree_energy_index": round(tree_energy, 2),
        "psychiatric_stress_weight": round(stress_weight, 2),
        "attachment_matrix_score": round(attachment, 2),
        "structural_sign": structural_sign,
        "cognitive_distortions": distortions,
    }
