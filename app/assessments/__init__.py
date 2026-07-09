from app.assessments.base import AssessmentItem, AssessmentInstrument, ResponseType
from app.assessments.clinical_screens import ISIInstrument, PCL5Instrument, PSSInstrument
from app.assessments.gad7 import GAD7Instrument
from app.assessments.micro_emotion import EmotionScaleInstrument
from app.assessments.phq9 import PHQ9Instrument
from app.assessments.projective import HTPProjectiveInstrument, TarotProjectiveInstrument
from app.assessments.registry import ASSESSMENT_DOMAINS, INSTRUMENT_PROFILES, all_instrument_ids, profile_summary
from app.assessments.school_probes import BehavioralActivationInstrument, CBThoughtInstrument, PsychodynamicInstrument
from app.assessments.wellbeing_screens import AttachmentECRInstrument, RSESInstrument

FORMAL_INSTRUMENTS = {
    "phq9": PHQ9Instrument(),
    "gad7": GAD7Instrument(),
    "isi": ISIInstrument(),
    "pss": PSSInstrument(),
    "pcl5": PCL5Instrument(),
    "rses": RSESInstrument(),
    "attachment_ecr": AttachmentECRInstrument(),
    "cbt_thought": CBThoughtInstrument(),
    "psychodynamic": PsychodynamicInstrument(),
    "behavioral": BehavioralActivationInstrument(),
    "htp": HTPProjectiveInstrument(),
    "tarot_reflect": TarotProjectiveInstrument(),
}

MICRO_INSTRUMENTS = {
    "micro_emotion": EmotionScaleInstrument(),
}

ALL_INSTRUMENTS = {
    **FORMAL_INSTRUMENTS,
    **MICRO_INSTRUMENTS,
}

__all__ = [
    "AssessmentItem",
    "AssessmentInstrument",
    "ResponseType",
    "ASSESSMENT_DOMAINS",
    "INSTRUMENT_PROFILES",
    "ALL_INSTRUMENTS",
    "profile_summary",
    "all_instrument_ids",
]
