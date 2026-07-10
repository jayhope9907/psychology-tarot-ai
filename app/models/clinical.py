from __future__ import annotations

from enum import Enum


class ClinicalSchool(str, Enum):
    """Major counseling theories and evidence-based approaches."""

    ROGERIAN = "ROGERIAN"
    BECK_CBT = "BECK_CBT"
    FREUDIAN = "FREUDIAN"
    ADLERIAN = "ADLERIAN"
    GESTALT = "GESTALT"
    EXISTENTIAL = "EXISTENTIAL"
    REALITY_THERAPY = "REALITY_THERAPY"
    SOLUTION_FOCUSED = "SOLUTION_FOCUSED"
    NARRATIVE = "NARRATIVE"
    EFT = "EFT"
    DBT = "DBT"
    ACT = "ACT"
    MOTIVATIONAL = "MOTIVATIONAL"
    IPT = "IPT"
    JUNGIAN = "JUNGIAN"
    BOWEN_SYSTEMS = "BOWEN_SYSTEMS"
    TRAUMA_INFORMED = "TRAUMA_INFORMED"
    MINDFULNESS = "MINDFULNESS"
    INTEGRATIVE = "INTEGRATIVE"


class MoodState(str, Enum):
    VULNERABLE = "VULNERABLE"
    ANALYTICAL = "ANALYTICAL"
    DEFENSIVE = "DEFENSIVE"
    NEUTRAL = "NEUTRAL"
