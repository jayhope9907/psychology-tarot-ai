from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ResponseType(str, Enum):
    LIKERT_0_3 = "likert_0_3"
    SCALE_0_10 = "scale_0_10"
    SINGLE_CHOICE = "single_choice"


LIKERT_0_3_OPTIONS = [
    {"value": 0, "label": "전혀 없음"},
    {"value": 1, "label": "며칠"},
    {"value": 2, "label": "절반 이상"},
    {"value": 3, "label": "거의 매일"},
]


@dataclass(frozen=True)
class AssessmentItem:
    instrument: str
    item_id: str
    prompt: str
    response_type: ResponseType
    options: List[Dict[str, Any]] = field(default_factory=list)
    conversational_framing: str = ""
    weight: float = 1.0


class AssessmentInstrument:
    instrument_id: str = ""
    display_name: str = ""

    def items(self) -> List[AssessmentItem]:
        raise NotImplementedError

    def score_partial(self, answers: Dict[str, int]) -> Dict[str, Any]:
        raise NotImplementedError

    def next_item(self, answers: Dict[str, int]) -> Optional[AssessmentItem]:
        for item in self.items():
            if item.item_id not in answers:
                return item
        return None

    def completion_rate(self, answers: Dict[str, int]) -> float:
        total = len(self.items())
        if total == 0:
            return 1.0
        return round(len(answers) / total, 2)
