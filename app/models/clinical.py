from __future__ import annotations

from enum import Enum


class ClinicalSchool(str, Enum):
    FREUDIAN = "FREUDIAN"
    ROGERIAN = "ROGERIAN"
    BECK_CBT = "BECK_CBT"


class MoodState(str, Enum):
    VULNERABLE = "VULNERABLE"
    ANALYTICAL = "ANALYTICAL"
    DEFENSIVE = "DEFENSIVE"
    NEUTRAL = "NEUTRAL"
