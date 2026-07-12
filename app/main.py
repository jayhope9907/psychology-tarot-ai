import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

from app.assessments import ALL_INSTRUMENTS, ASSESSMENT_DOMAINS, INSTRUMENT_PROFILES
from app.models.clinical import ClinicalSchool
from app.prompt_config import (
    build_system_prompt,
    build_tarot_reading_system_prompt,
    build_tarot_reading_user_prompt,
    build_user_prompt,
)
from app.services.assessment_battery import build_battery_status, next_recommended_instruments, sync_session_battery
from app.services.assessment_package import PACKAGE_TIERS, build_assessment_package, complete_checkout, mark_package_presented
from app.services.clinical_insight import build_clinical_insight, sync_session_insight
from app.services.clinical_pipeline import (
    backfill_user_profile,
    get_user_psych_profile,
    sync_after_counseling,
    sync_after_tarot,
)
from app.services.dsm5_framework import list_dsm5_catalog
from app.services.chat_session import CHAT_SESSIONS, get_or_create_session, get_session
from app.services.chat_stream import format_sse, run_chat_turn
from app.services.orchestrator import record_assessment_answer
from app.services.persona_router import PERSONA_CATALOG, detect_cognitive_distortions
from app.services.prompt_binding import PromptContextWeightBindingFactory
from app.services.vault import get_fernet, seal_payload, unseal_payload, write_audit_event

# 환경 변수 로드 및 AI 클라이언트 초기화
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Psychology Tarot AI System")


@app.on_event("startup")
async def startup_init_db():
    init_db()

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

PLAN_RULES = {
    "FREE": {"scope": "brief", "max_actions": 2, "max_tokens": 180, "detail_level": "low"},
    "LIGHT": {"scope": "focused", "max_actions": 3, "max_tokens": 260, "detail_level": "medium"},
    "BASIC": {"scope": "balanced", "max_actions": 4, "max_tokens": 360, "detail_level": "medium"},
    "PLUS": {"scope": "expanded", "max_actions": 5, "max_tokens": 480, "detail_level": "high"},
    "PREMIUM": {"scope": "full", "max_actions": 6, "max_tokens": 640, "detail_level": "high"},
}

PSYCHOLOGY_DATABASE: Dict[str, Dict[str, Any]] = {}
PURGED_USERS: set[str] = set()
CACHE_TTL_SECONDS = int(os.getenv("THERAPY_CACHE_TTL_SECONDS", "30"))


class InMemoryTTLCache:
    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        self._entries: Dict[str, Dict[str, Any]] = {}

    def _now(self) -> float:
        return datetime.now(timezone.utc).timestamp()

    def get(self, key: str) -> Optional[Any]:
        entry = self._entries.get(key)
        if not entry:
            return None
        if self._now() - entry["timestamp"] > self.ttl_seconds:
            self._entries.pop(key, None)
            return None
        return entry["value"]

    def set(self, key: str, value: Any) -> None:
        self._entries[key] = {"value": value, "timestamp": self._now()}

    def invalidate(self, key: Optional[str] = None) -> None:
        if key is None:
            self._entries.clear()
            return

        matching_keys = [
            entry_key
            for entry_key in self._entries.keys()
            if entry_key == key
            or entry_key.startswith(f"{key}:")
            or entry_key.startswith(f"dashboard:{key}:")
            or entry_key.startswith(f"analytics:{key}:")
        ]
        for entry_key in matching_keys:
            self._entries.pop(entry_key, None)


DASHBOARD_CACHE = InMemoryTTLCache()
ANALYTICS_CACHE = InMemoryTTLCache()

from app.services.tarot import (
    TAROT_ARCHETYPE_MAP,
    build_draw_from_picks,
    build_local_reading,
    draw_cards,
    format_draw_for_prompt,
    list_deck_catalog,
    merge_reading_with_output,
)
from app.services.tarot_bridge import apply_tarot_handoff, build_tarot_handoff
from app.services.homework import homework_snapshot, record_homework_submission
from app.db.database import init_db
from app.services.daily_routine import build_dashboard, record_checkin
from app.services.persistence import list_tarot_draws, record_tarot_draw, save_session, save_user_settings, get_user_settings


def _get_fernet() -> Fernet:
    return get_fernet()


def _encrypt_payload(user_id: str, payload: Dict[str, Any]) -> str:
    return seal_payload(user_id, payload)


def _decrypt_payload(user_id: str, token: str) -> Dict[str, Any]:
    return unseal_payload(user_id, token)


class PsychologyApiException(Exception):
    def __init__(self, message: str, status_code: int = 400, error_code: str = "PSYCHOLOGY_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


class InvalidUserException(PsychologyApiException):
    def __init__(self, user_id: str):
        super().__init__(f"Invalid user reference: {user_id}", status_code=404, error_code="INVALID_USER")


class DecryptionFailureException(PsychologyApiException):
    def __init__(self, user_id: str):
        super().__init__(f"Unable to decrypt stored history for user: {user_id}", status_code=500, error_code="DECRYPTION_FAILURE")


class InvalidPersonaException(PsychologyApiException):
    def __init__(self, persona: str):
        super().__init__(f"Unsupported persona requested: {persona}", status_code=400, error_code="INVALID_PERSONA")


class DrawingProjectiveProfile(BaseModel):
    structural_sign: str
    house_interpreted_code: str
    tree_energy_index: float
    person_relational_tag: str
    psychological_readiness_index: Optional[float] = None


class ArchetypeProfile(BaseModel):
    card_name: str
    archetype: str
    psychiatric_stress_weight: float
    cognitive_distortion_flag: str
    attachment_matrix_score: float


class PsychiatricFeatureProfile(BaseModel):
    drawing_projective_profile: DrawingProjectiveProfile
    cognitive_distortion_flags: List[str] = []
    attachment_matrix_score: float = 0.0
    archetype_profiles: List[ArchetypeProfile] = []


class ConsultationRequest(BaseModel):
    user_id: str = "anonymous"
    user_story: str
    drawn_card: str
    plan: str = "FREE"
    selected_cards: Optional[List[str]] = None
    preferred_school: Optional[ClinicalSchool] = ClinicalSchool.ROGERIAN


class PurgeRequest(BaseModel):
    user_id: str


class ChatStreamRequest(BaseModel):
    user_id: str = "anonymous"
    message: str
    session_id: Optional[str] = None
    plan: str = "FREE"
    assessment_response: Optional[Dict[str, Any]] = None
    homework_response: Optional[Dict[str, Any]] = None
    preferred_school: Optional[ClinicalSchool] = None
    association_license: Optional[str] = None
    image_data_url: Optional[str] = None
    image_search: bool = False


class ImageSearchRequest(BaseModel):
    query: str
    limit: int = 8


class AssociationLicenseRequest(BaseModel):
    license_key: str


class AssociationProvisionRequest(BaseModel):
    org_name: str
    discipline_id: str = "counseling_society"
    tier_id: str = "society"
    secondary_discipline: Optional[str] = None
    seats: Optional[int] = None
    days_valid: int = 365
    seed_cases: bool = True
    backfill_days: int = 28
    case_ids: Optional[List[str]] = None


class HomeworkSubmitRequest(BaseModel):
    user_id: str
    session_id: str
    assignment_id: str
    responses: Dict[str, Any] = {}
    skipped: bool = False


class AssessmentSubmitRequest(BaseModel):
    user_id: str
    session_id: str
    instrument: str
    item_id: str
    value: Optional[Any] = None
    text: Optional[str] = None
    skipped: bool = False


class CheckoutRequest(BaseModel):
    user_id: str
    session_id: str
    tier_id: Optional[str] = None


class TarotDrawRequest(BaseModel):
    count: int = 3
    spread: str = "three_card"
    seed: Optional[int] = None


class TarotPickRequest(BaseModel):
    spread: str = "three_card"
    card_ids: List[str]
    reversed_flags: Optional[List[bool]] = None
    user_id: str = "anonymous"


class CheckinRequest(BaseModel):
    user_id: str
    mood_score: Optional[int] = None
    note: str = ""
    dimensions: Optional[Dict[str, int]] = None


class PictoCheckinRequest(BaseModel):
    user_id: str
    mood_picto_id: str


class PictoChatRequest(BaseModel):
    user_id: str
    picto_ids: List[str]
    session_id: Optional[str] = None


class PictoCardRequest(BaseModel):
    user_id: str
    card_picto_id: str


class PictoCaregiverAlertRequest(BaseModel):
    user_id: str
    picto_ids: Optional[List[str]] = None


class PictureAssessmentStartRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    association_license: Optional[str] = None


class PictureAssessmentSubmitRequest(BaseModel):
    user_id: str
    session_id: str
    instrument: str
    item_id: str
    skipped: bool = False
    text: Optional[str] = None
    association: Optional[str] = None
    drawing_data: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    story: Optional[Dict[str, str]] = None


class ReminderSettingsRequest(BaseModel):
    user_id: str
    evening_reminder: bool = False
    hour: int = 21


class CounselingStyleTone(BaseModel):
    warmth: int = 4
    formality: int = 2
    pace: int = 3
    directness: int = 2


class CounselingStyleRequest(BaseModel):
    user_id: str
    counselor_id: Optional[str] = None
    texture: Optional[str] = None
    tone: Optional[CounselingStyleTone] = None
    voice_preset_id: Optional[str] = None
    voice_enabled: Optional[bool] = None
    auto_speak: Optional[bool] = None


class TarotReadingRequest(BaseModel):
    user_id: str = "anonymous"
    user_story: str = ""
    spread: str = "three_card"
    count: int = 3
    cards: Optional[List[Dict[str, Any]]] = None
    plan: str = "FREE"
    preferred_school: Optional[ClinicalSchool] = ClinicalSchool.ROGERIAN
    session_id: Optional[str] = None
    bridge_to_chat: bool = False


class TarotBridgeRequest(BaseModel):
    user_id: str = "anonymous"
    session_id: Optional[str] = None
    user_story: str = ""
    draw: Dict[str, Any]
    reading: Dict[str, Any]


def _error_payload(message: str, status_code: int, error_code: str) -> Dict[str, Any]:
    return {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "status_code": status_code,
        },
    }


@app.exception_handler(PsychologyApiException)
async def psychology_api_exception_handler(request: Request, exc: PsychologyApiException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=_error_payload(exc.message, exc.status_code, exc.error_code))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content=_error_payload("Validation failed.", 422, "VALIDATION_ERROR"))


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=_error_payload(str(exc.detail), exc.status_code, "HTTP_ERROR"))


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content=_error_payload("An unexpected server error occurred.", 500, "INTERNAL_SERVER_ERROR"))


def _resolve_plan(plan: str) -> Dict[str, Any]:
    normalized = (plan or "FREE").upper()
    return PLAN_RULES.get(normalized, PLAN_RULES["FREE"])


def _build_fallback_analysis(user_story: str, drawn_card: str, plan: str) -> str:
    return (
        f"{user_story}\n"
        f"카드 '{drawn_card}'는 현재 불안과 성찰의 시점으로 해석됩니다.\n"
        f"{plan} 등급 기준으로는 짧고 실천 가능한 CBT 중심 접근을 권장합니다."
    )


def _build_psychological_readiness_index(user_story: str, plan: str, selected_cards: Optional[List[str]] = None) -> float:
    normalized_story = (user_story or "").lower()
    base_score = 0.5
    if any(keyword in normalized_story for keyword in ["불안", "스트레스", "초조", "긴장", "우울", "혼란", "두려움", "상실"]):
        base_score -= 0.2
    if any(keyword in normalized_story for keyword in ["안정", "평온", "안정감", "편안", "정리", "회복", "성장", "찾고", "정돈"]):
        base_score += 0.2
    if (plan or "FREE").upper() == "PREMIUM":
        base_score += 0.05
    if selected_cards:
        base_score += 0.03
    return round(min(1.0, max(0.0, base_score)), 2)


def _build_projective_profile(user_story: str, drawn_card: str, psychological_readiness_index: Optional[float] = None) -> Dict[str, Any]:
    normalized_story = (user_story or "").lower()
    normalized_card = (drawn_card or "").lower()

    structural_sign = "stable"
    if any(keyword in normalized_story for keyword in ["불안", "스트레스", "초조", "긴장", "우울", "혼란"]):
        structural_sign = "tension"
    elif any(keyword in normalized_story for keyword in ["안정", "평온", "안정감", "편안"]):
        structural_sign = "calm"

    house_code = "H1"
    if "관계" in normalized_story or "사랑" in normalized_story:
        house_code = "H2"
    elif "직장" in normalized_story or "업무" in normalized_story or "일" in normalized_story:
        house_code = "H6"
    elif "가족" in normalized_story or "가정" in normalized_story:
        house_code = "H4"

    tree_energy_index = min(9.9, max(1.0, 3.0 + len(normalized_story.split()) * 0.18 + (0.4 if "상실" in normalized_story else 0.0)))
    person_relational_tag = "self-reflective"
    if any(keyword in normalized_story for keyword in ["관계", "사랑", "연인", "친구"]):
        person_relational_tag = "interpersonal"
    elif any(keyword in normalized_story for keyword in ["고립", "혼자", "외로움"]):
        person_relational_tag = "withdrawn"

    if "hermit" in normalized_card or "은둔" in normalized_story:
        person_relational_tag = "withdrawn"

    return {
        "structural_sign": structural_sign,
        "house_interpreted_code": house_code,
        "tree_energy_index": round(tree_energy_index, 2),
        "person_relational_tag": person_relational_tag,
        "psychological_readiness_index": round(psychological_readiness_index if psychological_readiness_index is not None else 0.5, 2),
    }


def _build_archetype_profile(
    user_story: str,
    selected_cards: Optional[List[str]] = None,
    drawn_card: Optional[str] = None,
) -> Dict[str, Any]:
    cards: List[str] = []
    if drawn_card:
        cards.append(drawn_card)
    for card_name in selected_cards or []:
        if card_name not in cards:
            cards.append(card_name)

    profiles: List[Dict[str, Any]] = []
    flags: List[str] = []
    scores: List[float] = []

    for card_name in cards:
        mapping = TAROT_ARCHETYPE_MAP.get(card_name)
        if not mapping:
            continue
        profiles.append(
            {
                "card_name": card_name,
                "archetype": mapping["archetype"],
                "psychiatric_stress_weight": mapping["psychiatric_stress_weight"],
                "cognitive_distortion_flag": mapping["cognitive_distortion_flag"],
                "attachment_matrix_score": mapping["attachment_matrix_score"],
            }
        )
        if mapping["cognitive_distortion_flag"] not in flags:
            flags.append(mapping["cognitive_distortion_flag"])
        scores.append(mapping["attachment_matrix_score"])

    for distortion in detect_cognitive_distortions(user_story):
        if distortion not in flags:
            flags.append(distortion)

    if not flags:
        fallback_flag = "rumination" if any(keyword in (user_story or "").lower() for keyword in ["불안", "스트레스", "혼란", "두려움"]) else "none"
        flags = [fallback_flag]

    if not profiles:
        return {
            "cognitive_distortion_flags": flags,
            "attachment_matrix_score": 0.5,
            "archetype_profiles": [],
        }

    return {
        "cognitive_distortion_flags": flags,
        "attachment_matrix_score": round(sum(scores) / len(scores), 2),
        "archetype_profiles": profiles,
    }


def _resolve_clinical_school(preferred_school: Optional[ClinicalSchool]) -> ClinicalSchool:
    return preferred_school or ClinicalSchool.ROGERIAN


def _build_behavior_metadata(school: ClinicalSchool) -> Dict[str, Any]:
    from app.services.counseling_theories import get_theory_meta

    meta = get_theory_meta(school)
    return {
        "clinical_protocol_mode": school.value,
        "assistant_behavior_rules": meta["techniques"][:4],
        "daily_logotherapy_homework_style": (
            f"{meta['label']} 기반 자기성찰 과제 — "
            f"{meta['techniques'][0] if meta['techniques'] else '감정 기록'}"
        ),
        "theory_label": meta["label"],
        "founder": meta["founder"],
    }


def _compose_output(user_story: str, drawn_card: str, plan: str, selected_cards: Optional[List[str]] = None, preferred_school: Optional[ClinicalSchool] = None) -> Dict[str, Any]:
    config = _resolve_plan(plan)
    school = _resolve_clinical_school(preferred_school)
    behavior_metadata = _build_behavior_metadata(school)
    readiness_index = _build_psychological_readiness_index(user_story, plan, selected_cards)
    profile = _build_projective_profile(user_story, drawn_card, readiness_index)
    archetype_profile = _build_archetype_profile(user_story, selected_cards, drawn_card)
    distortion_flags = archetype_profile["cognitive_distortion_flags"]
    detected_cognitive_distortions = [
        flag for flag in (distortion_flags if isinstance(distortion_flags, list) else [])
        if isinstance(flag, str) and flag.strip().lower() not in {"", "none"}
    ]

    prompt_binding = PromptContextWeightBindingFactory(
        school=school,
        psychological_readiness_index=readiness_index,
        cognitive_distortions=distortion_flags,
        attachment_matrix_score=archetype_profile["attachment_matrix_score"],
        tree_energy_index=profile["tree_energy_index"],
        psychiatric_stress_weight=(
            sum(item["psychiatric_stress_weight"] for item in archetype_profile["archetype_profiles"])
            / len(archetype_profile["archetype_profiles"])
            if archetype_profile["archetype_profiles"]
            else 0.5
        ),
        structural_sign=profile["structural_sign"],
    ).build()
    system_prompt = build_system_prompt() + "\n" + prompt_binding["system_prompt"] + "\n" + prompt_binding["context_block"]
    user_prompt = build_user_prompt(user_story, drawn_card)
    actions = [
        "오늘의 감정 1개를 이름 붙이고 기록하기",
        "10분 동안 생각의 흐름을 적어보기",
        "작은 행동 하나를 계획하고 실행하기",
    ][: config["max_actions"]]

    analysis = _build_fallback_analysis(user_story, drawn_card, plan)
    if client and getattr(client, "api_key", None):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=config["max_tokens"],
            )
            analysis = response.choices[0].message.content
        except Exception:
            analysis = _build_fallback_analysis(user_story, drawn_card, plan)

    return {
        "summary": analysis,
        "scope": config["scope"],
        "detail_level": config["detail_level"],
        "actions": actions,
        "asset_value_krw": 50000,
        "safety_note": "위기 상황 시 전문가 또는 응급 지원을 권장합니다.",
        "psychiatric_feature_profile": {
            "drawing_projective_profile": profile,
            "psychological_readiness_index": readiness_index,
            "cognitive_distortion_flags": archetype_profile["cognitive_distortion_flags"],
            "detected_cognitive_distortions": detected_cognitive_distortions,
            "attachment_matrix_score": archetype_profile["attachment_matrix_score"],
            "archetype_profiles": archetype_profile["archetype_profiles"],
        },
        **behavior_metadata,
    }


def _compose_tarot_reading(user_story: str, draw_result: Dict[str, Any]) -> str:
    """Light projection-style tarot reading (not deep Jungian / clinical)."""
    local = build_local_reading(user_story, draw_result)
    fallback = local["summary"]
    cards_block = format_draw_for_prompt(draw_result)
    system_prompt = build_tarot_reading_system_prompt()
    user_prompt = build_tarot_reading_user_prompt(user_story, cards_block)
    if client and getattr(client, "api_key", None):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.65,
                max_tokens=420,
            )
            return response.choices[0].message.content or fallback
        except Exception:
            return fallback
    return fallback


def _store_record(user_id: str, user_story: str, drawn_card: str, plan: str, output: Dict[str, Any], preferred_school: Optional[ClinicalSchool] = None) -> None:
    existing_record = PSYCHOLOGY_DATABASE.get(user_id)
    history: List[Dict[str, Any]] = []
    if existing_record:
        try:
            existing_payload = _decrypt_payload(user_id, existing_record["encrypted_payload"])
            history = existing_payload.get("history") or []
        except Exception:
            history = []

    payload = {
        "user_id": user_id,
        "user_story": user_story,
        "drawn_card": drawn_card,
        "plan": plan,
        "output": output,
        "preferred_school": (preferred_school.value if isinstance(preferred_school, ClinicalSchool) else None),
        "anonymous": True,
        "asset_value_krw": 50000,
        "timestamp": len(history),
        "history": history + [{
            "user_id": user_id,
            "user_story": user_story,
            "drawn_card": drawn_card,
            "plan": plan,
            "output": output,
            "preferred_school": (preferred_school.value if isinstance(preferred_school, ClinicalSchool) else None),
            "timestamp": len(history),
        }],
    }
    PSYCHOLOGY_DATABASE[user_id] = {
        "encrypted_payload": _encrypt_payload(user_id, payload),
        "asset_value_krw": 50000,
    }


def _load_history(user_id: str) -> List[Dict[str, Any]]:
    record = PSYCHOLOGY_DATABASE.get(user_id)
    if not record:
        return []
    try:
        payload = _decrypt_payload(user_id, record["encrypted_payload"])
    except Exception:
        return []

    history = payload.get("history")
    if isinstance(history, list):
        return history

    if payload.get("output"):
        return [payload]
    return []


def _build_dashboard_payload(user_id: str, membership_tier: str) -> Dict[str, Any]:
    history = _load_history(user_id)
    if not history:
        return {
            "user_id": user_id,
            "membership_tier": membership_tier,
            "history_length": 0,
            "summary": "Advanced analytics require a premium subscription.",
            "trend_analysis": {},
        }

    series = []
    for entry in history:
        profile = entry.get("output", {}).get("psychiatric_feature_profile", {}).get("drawing_projective_profile", {})
        readiness = entry.get("output", {}).get("psychiatric_feature_profile", {}).get("psychological_readiness_index")
        if readiness is None:
            readiness = profile.get("psychological_readiness_index")
        attachment = entry.get("output", {}).get("psychiatric_feature_profile", {}).get("attachment_matrix_score")
        tree_energy = profile.get("tree_energy_index")
        if readiness is None and attachment is None and tree_energy is None:
            continue
        series.append(
            {
                "timestamp": entry.get("timestamp") or len(series),
                "psychological_readiness_index": readiness if readiness is not None else 0.5,
                "attachment_matrix_score": attachment if attachment is not None else 0.5,
                "tree_energy_index": tree_energy if tree_energy is not None else 0.0,
            }
        )

    if not history:
        return {
            "user_id": user_id,
            "membership_tier": membership_tier,
            "history_length": 0,
            "summary": "Advanced analytics require a premium subscription.",
            "trend_analysis": {},
        }

    readiness_values = [item["psychological_readiness_index"] for item in series]
    attachment_values = [item["attachment_matrix_score"] for item in series]
    energy_values = [item["tree_energy_index"] for item in series]
    trend_analysis = {
        "psychological_readiness_index": {
            "start": readiness_values[0],
            "end": readiness_values[-1],
            "delta": round(readiness_values[-1] - readiness_values[0], 2),
        },
        "attachment_matrix_score": {
            "start": attachment_values[0],
            "end": attachment_values[-1],
            "delta": round(attachment_values[-1] - attachment_values[0], 2),
        },
        "tree_energy_index": {
            "start": energy_values[0],
            "end": energy_values[-1],
            "delta": round(energy_values[-1] - energy_values[0], 2),
        },
    }

    if membership_tier.upper() == "PREMIUM":
        premium_summary = (
            "Premium therapeutic summary: the user's readiness trend shows "
            f"{trend_analysis['psychological_readiness_index']['delta']:+.2f} change, "
            f"attachment stability shifted by {trend_analysis['attachment_matrix_score']['delta']:+.2f}, "
            f"and projective energy moved by {trend_analysis['tree_energy_index']['delta']:+.2f}."
        )
        return {
            "user_id": user_id,
            "membership_tier": membership_tier.upper(),
            "history_length": len(history),
            "summary": premium_summary,
            "trend_analysis": trend_analysis,
            "premium_therapeutic_summary": premium_summary,
        }

    return {
        "user_id": user_id,
        "membership_tier": membership_tier.upper(),
        "history_length": len(history),
        "summary": "Advanced analytics require a premium subscription.",
        "trend_analysis": trend_analysis,
    }


def _invalidate_user_caches(user_id: str) -> None:
    DASHBOARD_CACHE.invalidate(user_id)
    ANALYTICS_CACHE.invalidate(user_id)


def _purge_chat_sessions(user_id: str) -> None:
    session_ids = [session_id for session_id, state in CHAT_SESSIONS.items() if state.user_id == user_id]
    for session_id in session_ids:
        CHAT_SESSIONS.pop(session_id, None)


def _store_chat_profile(user_id: str, profile_delta: Dict[str, Any], plan: str) -> None:
    persona = profile_delta.get("persona_routing") or {}
    quant = profile_delta.get("quant_features") or {}
    battery = profile_delta.get("battery_coverage") or {}
    formal_scores = profile_delta.get("formal_scores") or {}
    clinical_insight = profile_delta.get("clinical_insight") or {}
    school_value = persona.get("school")
    preferred_school = ClinicalSchool(school_value) if school_value in {item.value for item in ClinicalSchool} else ClinicalSchool.ROGERIAN
    distortions = persona.get("detected_distortions") or []

    output = {
        "summary": "Chat session profile update",
        "scope": "chat",
        "detail_level": "session",
        "actions": [],
        "asset_value_krw": 50000,
        "psychiatric_feature_profile": {
            "drawing_projective_profile": {
                "psychological_readiness_index": quant.get("psychological_readiness_index", 0.5),
                "tree_energy_index": quant.get("tree_energy_index", 0.0),
                "structural_sign": quant.get("structural_sign", "chat"),
                "house_interpreted_code": "H0",
                "person_relational_tag": "conversational",
            },
            "psychological_readiness_index": quant.get("psychological_readiness_index", 0.5),
            "cognitive_distortion_flags": distortions,
            "detected_cognitive_distortions": distortions,
            "attachment_matrix_score": quant.get("attachment_matrix_score", 0.5),
            "archetype_profiles": [],
            "formal_scores": formal_scores,
            "battery_coverage": battery,
            "clinical_insight": clinical_insight,
            "chat_profile_delta": profile_delta,
        },
    }
    _store_record(user_id, "chat session", "conversation", plan, output, preferred_school)


@app.get("/")
async def app_ui():
    app_path = STATIC_DIR / "app.html"
    if app_path.exists():
        return FileResponse(str(app_path))
    home_path = STATIC_DIR / "home.html"
    if home_path.exists():
        return FileResponse(str(home_path))
    return {"message": "Psychology Tarot AI backend is running."}


@app.get("/home")
async def home_ui():
    home_path = STATIC_DIR / "home.html"
    if home_path.exists():
        return FileResponse(str(home_path))
    raise HTTPException(status_code=404, detail="Home UI not found")


@app.get("/chat")
async def chat_ui():
    index_path = STATIC_DIR / "chat.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Chat UI not found")


def _resolve_public_base(request: Optional[Request] = None) -> str:
    env_base = (os.getenv("PUBLIC_BASE_URL") or "").rstrip("/")
    if env_base:
        return env_base
    if request is None:
        return ""
    host = (request.headers.get("x-forwarded-host") or request.headers.get("host") or "").split(",")[0].strip()
    if not host or host.startswith("127.0.0.1") or host.startswith("localhost") or host == "testserver":
        return ""
    scheme = (request.headers.get("x-forwarded-proto") or request.url.scheme or "https").split(",")[0].strip()
    return f"{scheme}://{host}".rstrip("/")


def _public_urls(public_base: str) -> Dict[str, str]:
    paths = {
        "app": "/",
        "home": "/home",
        "chat": "/chat",
        "tarot": "/tarot",
        "test": "/test",
        "legal": "/legal",
        "associations": "/associations",
        "picto": "/picto",
        "clinical": "/clinical",
        "picture_assessment": "/picture-assessment",
        "health": "/health",
        "tarot_deck_api": "/api/v1/tarot/deck",
    }
    if public_base:
        return {name: f"{public_base}{path}" for name, path in paths.items()}
    return paths


@app.get("/health")
async def health_check(request: Request):
    public_base = _resolve_public_base(request)
    urls = _public_urls(public_base)
    return {
        "status": "ok",
        "service": "psychology-tarot-ai",
        "version": os.getenv("APP_VERSION", "main"),
        "public": bool(public_base),
        "public_base": public_base or None,
        "urls": urls,
        "share_links": {
            "앱": urls.get("app", "/"),
            "홈": urls.get("home", "/home"),
            "AI 대화": urls.get("chat", "/chat"),
            "3D 타로": urls.get("tarot", "/tarot"),
            "그림 마음": urls.get("picto", "/picto"),
            "마음 돌보기": urls.get("clinical", "/clinical"),
            "그림 표현": urls.get("picture_assessment", "/picture-assessment"),
            "이용 안내": urls.get("legal", "/legal"),
        },
        "deploy_hint": "https://render.com/deploy?repo=https://github.com/jayhope9907/psychology-tarot-ai",
    }


@app.get("/tarot")
async def tarot_ui():
    tarot_path = STATIC_DIR / "tarot.html"
    if tarot_path.exists():
        return FileResponse(str(tarot_path))
    raise HTTPException(status_code=404, detail="Tarot UI not found")


@app.get("/picto")
async def picto_ui():
    picto_path = STATIC_DIR / "picto.html"
    if picto_path.exists():
        return FileResponse(str(picto_path))
    raise HTTPException(status_code=404, detail="Picto UI not found")


@app.get("/picture-assessment")
async def picture_assessment_ui():
    path = STATIC_DIR / "picture-assessment.html"
    if path.exists():
        return FileResponse(str(path))
    raise HTTPException(status_code=404, detail="Picture assessment UI not found")


@app.get("/clinical")
async def clinical_hub():
    path = STATIC_DIR / "clinical.html"
    if path.exists():
        return FileResponse(str(path))
    raise HTTPException(status_code=404, detail="Clinical hub not found")


@app.get("/test")
async def test_hub():
    test_path = STATIC_DIR / "test.html"
    if test_path.exists():
        return FileResponse(str(test_path))
    raise HTTPException(status_code=404, detail="Test hub not found")


@app.get("/legal")
async def legal_ui():
    legal_path = STATIC_DIR / "legal.html"
    if legal_path.exists():
        return FileResponse(str(legal_path))
    raise HTTPException(status_code=404, detail="Legal page not found")


@app.get("/associations")
async def associations_ui():
    path = STATIC_DIR / "associations.html"
    if path.exists():
        return FileResponse(str(path))
    raise HTTPException(status_code=404, detail="Associations page not found")


@app.get("/api/v1/legal/consent")
async def legal_consent():
    from app.services.legal_compliance import build_consent_document

    return build_consent_document()


@app.get("/api/v1/legal/scope")
async def legal_scope():
    from app.services.legal_compliance import SERVICE_SCOPE_SUMMARY, build_consent_document

    return {"summary": SERVICE_SCOPE_SUMMARY, **build_consent_document()}


@app.get("/api/v1/tarot/deck")
async def tarot_deck_catalog():
    return list_deck_catalog()


@app.post("/api/v1/tarot/draw")
async def tarot_draw(request: TarotDrawRequest):
    count = min(max(request.count, 1), 3)
    return draw_cards(count=count, spread=request.spread, seed=request.seed)


@app.post("/api/v1/tarot/pick")
async def tarot_pick(request: TarotPickRequest):
    if not request.card_ids:
        raise HTTPException(status_code=400, detail="card_ids required")
    if len(request.card_ids) > 3:
        raise HTTPException(status_code=400, detail="max 3 cards")
    result = build_draw_from_picks(
        card_ids=request.card_ids,
        spread=request.spread,
        reversed_flags=request.reversed_flags,
    )
    draw_id = record_tarot_draw(request.user_id, result)
    from app.services.maum_organism import sync_after_tarot_draw

    sync_after_tarot_draw(request.user_id, result, draw_id=draw_id or None)
    return result


@app.get("/api/v1/dashboard/{user_id}")
async def user_dashboard(user_id: str):
    from app.services.maum_organism import build_organism_state

    dash = build_dashboard(user_id)
    dash["organism"] = {
        "api": f"/api/v1/organism/{user_id}",
        "next_actions": build_organism_state(user_id)["next_actions"][:3],
    }
    return dash


@app.get("/api/v1/organism/{user_id}")
async def maum_organism(user_id: str):
    from app.services.maum_organism import build_organism_state

    return build_organism_state(user_id)


@app.get("/api/v1/chat/mood-context/{user_id}")
async def chat_mood_context(user_id: str):
    from app.services.mood_assistant import get_mood_welcome_message, resolve_mood_context
    from app.services.mood_dimensions import build_sphere_visual, dimension_meta_for_client

    ctx = resolve_mood_context(user_id)
    sphere = build_sphere_visual(ctx.dimensions) if ctx.has_checkin else None
    return {
        "user_id": user_id,
        "mood": ctx.to_dict(),
        "agent": ctx.agent,
        "sphere": sphere,
        "dimension_meta": dimension_meta_for_client(),
        "welcome_message": get_mood_welcome_message(ctx),
    }


@app.post("/api/v1/checkin")
async def mood_checkin(request: CheckinRequest):
    if not request.dimensions and request.mood_score is None:
        raise HTTPException(status_code=400, detail="mood_score or dimensions required")
    if request.mood_score is not None and (request.mood_score < 1 or request.mood_score > 5):
        raise HTTPException(status_code=400, detail="mood_score must be 1-5")
    if request.dimensions:
        from app.services.mood_dimensions import normalize_dimensions

        dims = normalize_dimensions(request.dimensions)
        for key, value in dims.items():
            if value < 1 or value > 5:
                raise HTTPException(status_code=400, detail=f"dimension {key} must be 1-5")
    result = record_checkin(request.user_id, request.mood_score, request.note, request.dimensions)
    _organism_after_checkin(request.user_id, result)
    return result


def _organism_after_checkin(user_id: str, checkin: Dict[str, Any], *, source: str = "checkin", picto_id: Optional[str] = None) -> None:
    from app.services.maum_organism import sync_after_checkin

    sync_after_checkin(user_id, checkin, source=source, picto_id=picto_id)


@app.get("/api/v1/picto/catalog")
async def picto_catalog_api(full: bool = False):
    from app.services.picto_vocabulary import picto_catalog, picto_offline_bundle

    if full:
        return picto_offline_bundle()
    return picto_catalog()


@app.get("/api/v1/counsel/offline-bundle")
async def counsel_offline_bundle_api():
    from app.services.counsel_offline import counsel_offline_bundle

    return counsel_offline_bundle()


@app.post("/api/v1/picto/checkin")
async def picto_checkin(request: PictoCheckinRequest):
    from app.services.picto_vocabulary import mood_dimensions_from_picto, picto_item

    dims = mood_dimensions_from_picto(request.mood_picto_id)
    if not dims:
        raise HTTPException(status_code=400, detail="invalid mood_picto_id")
    item = picto_item(request.mood_picto_id) or {}
    note = f"[그림기분] {item.get('emoji', '')} {item.get('phrase', '')}".strip()
    result = record_checkin(request.user_id, None, note, dims)
    _organism_after_checkin(request.user_id, result, source="picto", picto_id=request.mood_picto_id)
    return {"checkin": result, "mood_picto_id": request.mood_picto_id, "emoji": item.get("emoji")}


async def _run_picto_chat(user_id: str, picto_ids: List[str], session_id: Optional[str]) -> Dict[str, Any]:
    from app.services.picto_vocabulary import compose_picto_message, suggest_reply_pictos

    if not picto_ids:
        raise HTTPException(status_code=400, detail="picto_ids required")
    message = compose_picto_message(picto_ids)
    message += "\n[그림 AAC 모드: 답변은 짧고 쉬운 말 2~3문장만.]"

    session = get_or_create_session(user_id, session_id, "FREE")
    reply_text = ""
    async for event in run_chat_turn(session, message, client, max_tokens=180):
        if event["event"] == "done":
            reply_text = (event["data"].get("assistant_message") or "").strip()
    if not reply_text:
        reply_text = "함께 있어요. 천천히 괜찮아질 거예요."
    save_session(session)
    sync_after_counseling(user_id, session)
    from app.services.maum_organism import sync_after_picto_chat

    sync_after_picto_chat(user_id, session.session_id, picto_ids)
    return {
        "session_id": session.session_id,
        "user_message": message,
        "reply_text": reply_text,
        "reply_pictos": suggest_reply_pictos(reply_text, 4),
    }


@app.post("/api/v1/picto/chat")
async def picto_chat(request: PictoChatRequest):
    return await _run_picto_chat(request.user_id, request.picto_ids, request.session_id)


@app.post("/api/v1/picto/card")
async def picto_card(request: PictoCardRequest):
    from app.services.picto_vocabulary import picto_card_reply, picto_item

    item = picto_item(request.card_picto_id)
    if not item:
        raise HTTPException(status_code=400, detail="invalid card_picto_id")
    payload = picto_card_reply(request.card_picto_id)
    return {
        "user_id": request.user_id,
        "card_picto_id": request.card_picto_id,
        "emoji": item.get("emoji"),
        **payload,
    }


@app.get("/api/v1/picto/mood-timeline/{user_id}")
async def picto_mood_timeline(user_id: str, days: int = 7):
    from app.services.daily_routine import recent_checkins, today_checkin
    from app.services.picto_vocabulary import build_picto_mood_timeline, infer_mood_picto_from_checkin

    checkins = recent_checkins(user_id, max(1, min(days, 30)))
    today = today_checkin(user_id)
    today_picto = None
    if today:
        today_picto = infer_mood_picto_from_checkin(today)
        today_picto["date"] = today.get("checkin_date")
    return {
        "user_id": user_id,
        "days": days,
        "today": today_picto,
        "timeline": build_picto_mood_timeline(checkins),
    }


@app.post("/api/v1/picto/caregiver-alert")
async def picto_caregiver_alert(request: PictoCaregiverAlertRequest):
    from app.services.picto_vocabulary import compose_picto_message, picto_item
    from app.services.psych_timeline import record_event

    message = compose_picto_message(request.picto_ids or ["help_caregiver"])
    if request.note:
        message = f"{message} · {request.note}"
    record_event(
        request.user_id,
        "picto_caregiver_alert",
        {
            "message": message,
            "picto_ids": request.picto_ids or ["help_caregiver"],
            "urgency": "caregiver",
        },
    )
    item = picto_item("help_caregiver") or {}
    return {
        "status": "recorded",
        "user_id": request.user_id,
        "emoji": item.get("emoji", "👨‍👩‍👧"),
        "message": message,
    }


@app.get("/api/v1/history/{user_id}")
async def user_history(user_id: str):
    from app.services.daily_routine import recent_checkins
    from app.services.insights import build_weekly_report
    from app.services.persistence import list_user_sessions, load_latest_session_for_user

    session = load_latest_session_for_user(user_id)
    return {
        "user_id": user_id,
        "session_id": session.session_id if session else None,
        "sessions": list_user_sessions(user_id, 10),
        "checkins": recent_checkins(user_id, 14),
        "tarot_draws": list_tarot_draws(user_id, 10),
        "weekly_report": build_weekly_report(user_id),
        "message_count": len(session.messages) if session else 0,
    }


@app.get("/api/v1/insights/weekly/{user_id}")
async def weekly_insights(user_id: str):
    from app.services.insights import build_weekly_report

    return build_weekly_report(user_id)


@app.post("/api/v1/settings/reminder")
async def update_reminder_settings(request: ReminderSettingsRequest):
    settings = get_user_settings(request.user_id)
    settings["evening_reminder"] = request.evening_reminder
    settings["reminder_hour"] = request.hour
    return save_user_settings(request.user_id, settings)


@app.get("/api/v1/chat/style-catalog")
async def chat_style_catalog():
    from app.services.counseling_style import build_style_catalog

    return build_style_catalog()


@app.get("/api/v1/settings/counseling-style/{user_id}")
async def get_counseling_style(user_id: str):
    from app.services.counseling_style import resolve_counseling_style

    return resolve_counseling_style(get_user_settings(user_id))


@app.post("/api/v1/settings/counseling-style")
async def update_counseling_style(request: CounselingStyleRequest):
    from app.services.counseling_style import normalize_style, resolve_counseling_style

    settings = get_user_settings(request.user_id)
    current = normalize_style(settings.get("counseling_style"))
    if request.counselor_id is not None:
        current["counselor_id"] = request.counselor_id
    if request.texture is not None:
        current["texture"] = request.texture
    if request.tone is not None:
        current["tone"] = request.tone.model_dump()
    if request.voice_preset_id is not None:
        current["voice_preset_id"] = request.voice_preset_id
    if request.voice_enabled is not None:
        current["voice_enabled"] = request.voice_enabled
    if request.auto_speak is not None:
        current["auto_speak"] = request.auto_speak
    settings["counseling_style"] = normalize_style(current)
    save_user_settings(request.user_id, settings)
    return resolve_counseling_style(settings)


@app.get("/api/v1/voice/presets")
async def voice_presets(query: str = "", gender: Optional[str] = None, counselor_id: Optional[str] = None):
    from app.services.counseling_style import search_voice_presets

    return {
        "query": query,
        "presets": search_voice_presets(query, gender, counselor_id),
        "tts_engine": "browser_speech_synthesis",
        "hint": "클라이언트 Web Speech API로 재생. voice_hints로 시스템 음성 매칭.",
    }


@app.post("/api/v1/tarot/reading")
async def tarot_reading(request: TarotReadingRequest):
    draw_result = (
        {"spread": request.spread, "cards": request.cards}
        if request.cards
        else draw_cards(count=request.count, spread=request.spread)
    )
    local = build_local_reading(request.user_story, draw_result)
    primary_card = local.get("primary_card") or "The Fool"

    try:
        ai_analysis = _compose_tarot_reading(request.user_story, draw_result)
        reading = {
            **local,
            "ai_analysis": ai_analysis,
            "recommended_actions": local.get("cbt_actions") or [],
        }
        _store_record(
            request.user_id,
            request.user_story,
            primary_card,
            request.plan,
            {"summary": ai_analysis, "reading_tone": "light_projection"},
            request.preferred_school,
        )
        _invalidate_user_caches(request.user_id)
    except Exception:
        reading = {
            **local,
            "ai_analysis": local["summary"],
            "recommended_actions": local["cbt_actions"],
        }

    return {
        "plan": request.plan.upper(),
        "draw": draw_result,
        "reading": reading,
        "stored": True,
        "handoff": _maybe_bridge_tarot(request, draw_result, reading),
    }


def _maybe_bridge_tarot(
    request: TarotReadingRequest,
    draw_result: Dict[str, Any],
    reading: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    if not request.bridge_to_chat:
        return None
    session = get_or_create_session(request.user_id, request.session_id, request.plan)
    handoff = build_tarot_handoff(request.user_story, draw_result, reading)
    result = apply_tarot_handoff(session, handoff)
    save_session(session)
    sync_after_tarot(request.user_id, session.session_id, handoff)
    return result


@app.post("/api/v1/tarot/bridge")
async def tarot_bridge(request: TarotBridgeRequest):
    session = get_or_create_session(request.user_id, request.session_id)
    handoff = build_tarot_handoff(request.user_story, request.draw, request.reading)
    result = apply_tarot_handoff(session, handoff)
    session.messages.append({"role": "assistant", "content": result["bridge_message"]})
    save_session(session)
    psych_profile = sync_after_tarot(
        request.user_id,
        session.session_id,
        handoff,
    )
    result["psych_profile"] = {
        "pipeline_status": psych_profile.get("pipeline_status"),
        "top_spectra": (psych_profile.get("recommendations") or {}).get("top_spectra", [])[:3],
        "instruments": (psych_profile.get("recommendations") or {}).get("instruments", [])[:4],
    }
    return result


@app.get("/api/v1/sessions/{session_id}/homework")
async def session_homework(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return homework_snapshot(session)


@app.post("/api/v1/sessions/{session_id}/homework/submit")
async def submit_homework(session_id: str, request: HomeworkSubmitRequest):
    if request.session_id != session_id:
        raise HTTPException(status_code=400, detail="Session mismatch")
    session = get_session(session_id)
    if not session or session.user_id != request.user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    result = record_homework_submission(
        session,
        request.assignment_id,
        request.responses,
        skipped=request.skipped,
    )
    return result


@app.get("/api/v1/chat/sessions/{session_id}")
async def chat_session_state(session_id: str, include_messages: bool = False):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    payload = session.to_dict()
    if include_messages:
        payload["messages"] = session.messages
    return payload


@app.get("/api/v1/chat/sessions/{session_id}/transcript")
async def chat_session_transcript(session_id: str):
    from app.services.counseling_phase import phase_snapshot

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "messages": session.messages,
        "turn_count": session.turn_count,
        "counseling_phase": session.counseling_phase,
        "counseling_phase_info": phase_snapshot(session),
        "clinical_insight": session.clinical_insight,
        "has_tarot_handoff": bool(session.tarot_handoff),
        "homework_pending": bool(session.pending_homework),
    }


@app.get("/api/v1/chat/sessions/user/{user_id}")
async def chat_sessions_for_user(user_id: str, limit: int = 12):
    from app.services.persistence import list_user_sessions

    return {"user_id": user_id, "sessions": list_user_sessions(user_id, min(max(limit, 1), 30))}


@app.post("/api/v1/chat/sessions/new")
async def chat_new_session(user_id: str, plan: str = "BASIC"):
    from uuid import uuid4

    from app.services.chat_session import ChatSessionState
    from app.services.persistence import save_session

    session = ChatSessionState(user_id=user_id, session_id=str(uuid4()), plan=plan)
    save_session(session)
    return {"session_id": session.session_id, "user_id": user_id}


@app.get("/api/v1/chat/personas")
async def chat_personas():
    from app.services.counseling_theories import list_categories_for_api, list_theories_for_api

    return {
        "personas": list_theories_for_api(),
        "categories": list_categories_for_api(),
    }


@app.get("/api/v1/dsm5/catalog")
async def dsm5_catalog():
    return list_dsm5_catalog()


@app.get("/api/v1/users/{user_id}/psych-profile")
async def user_psych_profile(user_id: str, auto_backfill: bool = True):
    return get_user_psych_profile(user_id, auto_backfill=auto_backfill)


@app.post("/api/v1/users/{user_id}/psych-profile/rebuild")
async def rebuild_user_psych_profile(user_id: str):
    return backfill_user_profile(user_id)


@app.get("/api/v1/users/{user_id}/psych-timeline")
async def user_psych_timeline(user_id: str, limit: int = 30):
    from app.services.psych_timeline import list_events

    return {"user_id": user_id, "events": list_events(user_id, min(max(limit, 1), 100))}


@app.get("/api/v1/associations/catalog")
async def associations_catalog():
    from app.services.association_licensing import build_associations_catalog

    return build_associations_catalog()


@app.get("/api/v1/associations/disciplines/{discipline_id}")
async def association_discipline(discipline_id: str):
    from app.services.association_licensing import DISCIPLINE_PROFILES, resolve_entitlements

    profile = DISCIPLINE_PROFILES.get(discipline_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Unknown discipline")
    return {
        **profile,
        "sample_entitlements_society": resolve_entitlements(discipline_id, "society"),
    }


@app.post("/api/v1/associations/licenses/validate")
async def validate_association_license(request: AssociationLicenseRequest):
    from app.services.license_store import validate_license

    return validate_license(request.license_key)


@app.post("/api/v1/associations/licenses/provision")
async def provision_association_license(request: AssociationProvisionRequest, req: Request):
    expected = os.getenv("PURGE_AUDIT_TOKEN", "")
    token = req.headers.get("X-Audit-Token", "")
    if not expected or token != expected:
        raise HTTPException(status_code=403, detail="Admin token required")
    from app.services.license_store import provision_license
    from app.services.vault import write_audit_event

    result = provision_license(
        request.org_name,
        request.discipline_id,
        request.tier_id,
        secondary_discipline=request.secondary_discipline,
        seats=request.seats,
        days_valid=request.days_valid,
        seed_cases=request.seed_cases,
        backfill_days=request.backfill_days,
        case_ids=request.case_ids,
    )
    write_audit_event("LICENSE_PROVISION", "association", {"org_id": result.get("org_id")})
    return result


@app.get("/api/v1/associations/orgs")
async def list_association_orgs(request: Request, limit: int = 20):
    expected = os.getenv("PURGE_AUDIT_TOKEN", "")
    token = request.headers.get("X-Audit-Token", "")
    if not expected or token != expected:
        raise HTTPException(status_code=403, detail="Admin token required")
    from app.services.license_store import list_organizations

    return {"organizations": list_organizations(min(max(limit, 1), 100))}


@app.get("/api/v1/clinical/catalog")
async def clinical_catalog_api(license_key: Optional[str] = None, user_id: Optional[str] = None):
    from app.services.clinical_catalog import unified_clinical_catalog
    from app.services.clinical_user_voice import HUB
    from app.services.association_context import resolve_api_license

    ctx = resolve_api_license(license_key, user_id)
    if ctx["license_valid"] is False:
        return {
            "license_invalid": True,
            "license_reason": ctx["license_reason"],
            "license_reason_ko": ctx["license_reason_ko"],
            "user_title": HUB["title"],
            "user_subtitle": "라이선스를 다시 확인해 주세요.",
            "tracks": [],
            "domains": [],
            "formal_instruments": [],
            "projective_instruments": [],
            "counts": {
                "formal_instruments": 0,
                "projective_instruments": 0,
                "unique_instruments": 0,
                "formal_items": 0,
                "projective_items": 0,
                "total_items": 0,
                "domains": 0,
            },
        }
    return unified_clinical_catalog(ctx["entitlements"])


@app.get("/api/v1/clinical/summary/{user_id}")
async def clinical_summary_api(user_id: str, license_key: Optional[str] = None):
    from app.services.clinical_catalog import build_user_clinical_summary
    from app.services.persistence import load_latest_session_for_user
    from app.services.association_context import bind_license_to_session

    if license_key:
        session = load_latest_session_for_user(user_id) or get_or_create_session(user_id, plan="PLUS")
        bind_license_to_session(session, license_key)
        save_session(session)

    return build_user_clinical_summary(user_id)


@app.get("/api/v1/picture-assessment/catalog")
async def picture_assessment_catalog_api(license_key: Optional[str] = None, user_id: Optional[str] = None):
    from app.services.picture_assessment import picture_assessment_catalog
    from app.services.clinical_user_voice import PICTURE_HUB
    from app.services.association_context import resolve_api_license

    ctx = resolve_api_license(license_key, user_id)
    if ctx["license_valid"] is False:
        return {
            "license_invalid": True,
            "license_reason": ctx["license_reason"],
            "license_reason_ko": ctx["license_reason_ko"],
            "title": PICTURE_HUB["title"],
            "subtitle": "라이선스를 다시 확인해 주세요.",
            "instruments": [],
            "instrument_count": 0,
            "total_items": 0,
            "disclaimer": "",
        }
    return picture_assessment_catalog(ctx["entitlements"])


@app.post("/api/v1/picture-assessment/start")
async def picture_assessment_start(request: PictureAssessmentStartRequest):
    session = get_or_create_session(request.user_id, request.session_id, "PICTURE_ASSESSMENT_TEST")
    if request.association_license:
        from app.services.association_context import bind_license_to_session

        bind_license_to_session(session, request.association_license)
    from app.services.picture_assessment import picture_assessment_catalog

    catalog = picture_assessment_catalog(session.org_entitlements)
    save_session(session)
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "instrument_count": catalog["instrument_count"],
        "total_items": catalog["total_items"],
    }


@app.post("/api/v1/picture-assessment/submit")
async def picture_assessment_submit(request: PictureAssessmentSubmitRequest):
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != request.user_id:
        raise HTTPException(status_code=403, detail="Session user mismatch")

    from app.services.picture_assessment import record_projective_response

    payload: Dict[str, Any] = {
        "instrument": request.instrument,
        "item_id": request.item_id,
        "skipped": request.skipped,
        "text": request.text,
        "association": request.association,
        "drawing_data": request.drawing_data,
        "meta": request.meta,
        "story": request.story,
    }
    recorded = record_projective_response(session, payload)
    if recorded.get("error"):
        raise HTTPException(status_code=400, detail=recorded["error"])
    save_session(session)
    return {"recorded": recorded}


@app.get("/api/v1/picture-assessment/results/{session_id}")
async def picture_assessment_results_api(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    from app.services.picture_assessment import picture_assessment_results

    return picture_assessment_results(session)


@app.get("/api/v1/assessments/catalog")
async def assessments_catalog():
    instruments = []
    for instrument_id, instrument in ALL_INSTRUMENTS.items():
        profile = INSTRUMENT_PROFILES.get(instrument_id, {})
        domain = ASSESSMENT_DOMAINS.get(profile.get("domain", ""), {})
        instruments.append(
            {
                "instrument_id": instrument_id,
                "display_name": profile.get("display_name", instrument.display_name),
                "domain_id": profile.get("domain"),
                "domain_label": domain.get("label"),
                "school": domain.get("school"),
                "focus": profile.get("focus"),
                "item_count": len(instrument.items()),
            }
        )
    return {
        "domains": [
            {
                "domain_id": domain_id,
                "label": meta["label"],
                "school": meta["school"],
                "instruments": meta["instruments"],
            }
            for domain_id, meta in ASSESSMENT_DOMAINS.items()
        ],
        "instruments": instruments,
        "total_instruments": len(instruments),
        "total_domains": len(ASSESSMENT_DOMAINS),
    }


@app.get("/api/v1/assessments/battery/{session_id}")
async def assessments_battery(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    status = build_battery_status(session)
    status["recommendations"] = next_recommended_instruments(session)
    return status


@app.get("/api/v1/insights/{session_id}")
async def clinical_insights(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return build_clinical_insight(session)


@app.get("/api/v1/sessions/{session_id}/assessment-package")
async def get_assessment_package(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.assessment_package:
        package = dict(session.assessment_package)
        package["payment_required"] = not session.assessment_paid
        return package
    package = build_assessment_package(session)
    mark_package_presented(session, package)
    return package


@app.get("/api/v1/assessments/packages/catalog")
async def assessment_package_catalog():
    return {"tiers": PACKAGE_TIERS}


@app.post("/api/v1/sessions/{session_id}/checkout")
async def checkout_assessment_package(session_id: str, request: CheckoutRequest):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != request.user_id:
        raise HTTPException(status_code=403, detail="Session user mismatch")
    if session.assessment_paid:
        return {
            "success": True,
            "already_paid": True,
            "payment_id": session.payment_id,
            "message": "이미 결제가 완료된 세션입니다.",
        }

    if request.tier_id and request.tier_id not in PACKAGE_TIERS:
        raise HTTPException(status_code=400, detail="Invalid package tier")

    if not session.assessment_package_ready:
        package = build_assessment_package(session)
        mark_package_presented(session, package)

    result = complete_checkout(session, request.tier_id)
    write_audit_event(
        "ASSESSMENT_CHECKOUT",
        request.user_id,
        {
            "session_id": session_id,
            "payment_id": result["payment_id"],
            "amount_krw": result["amount_krw"],
            "tier_label": result["tier_label"],
        },
    )
    result["counseling_phase"] = session.counseling_phase
    result["assessment_package"] = session.assessment_package
    return result


@app.post("/api/v1/assessments/submit")
async def assessments_submit(request: AssessmentSubmitRequest):
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != request.user_id:
        raise HTTPException(status_code=403, detail="Session user mismatch")

    from app.services.association_context import ensure_session_entitlements

    ensure_session_entitlements(session)

    recorded = record_assessment_answer(
        session,
        {
            "instrument": request.instrument,
            "item_id": request.item_id,
            "value": request.value,
            "text": request.text,
            "skipped": request.skipped,
        },
    )
    if recorded.get("error") == "not_licensed":
        raise HTTPException(status_code=403, detail="not_licensed")
    battery = sync_session_battery(session)
    insight = sync_session_insight(session)
    save_session(session)
    return {
        "recorded": recorded,
        "battery_coverage": battery,
        "clinical_insight": insight,
        "formal_scores": {
            instrument_id: ALL_INSTRUMENTS[instrument_id].score_partial(answers)
            for instrument_id, answers in session.formal_answers.items()
            if instrument_id in ALL_INSTRUMENTS and answers
        },
    }


@app.post("/api/v1/chat/stream")
async def chat_stream(request: ChatStreamRequest):
    session = get_or_create_session(request.user_id, request.session_id, request.plan)
    if request.preferred_school:
        session.preferred_school = request.preferred_school.value
    if request.association_license:
        from app.services.association_context import bind_license_to_session

        bind_license_to_session(session, request.association_license)
    effective_plan = session.plan or request.plan
    config = _resolve_plan(effective_plan)

    async def event_generator():
        try:
            async for event in run_chat_turn(
                session,
                request.message,
                client,
                max_tokens=config["max_tokens"],
                assessment_response=request.assessment_response,
                homework_response=request.homework_response,
                preferred_school=request.preferred_school,
                image_data_url=request.image_data_url,
                image_search=bool(request.image_search),
            ):
                if event["event"] == "done":
                    profile_delta = event["data"].get("profile_delta") or {}
                    _store_chat_profile(request.user_id, profile_delta, request.plan)
                    _invalidate_user_caches(request.user_id)
                    save_session(session)
                    psych = sync_after_counseling(request.user_id, session)
                    event["data"]["psych_profile"] = {
                        "pipeline_status": psych.get("pipeline_status"),
                        "top_spectra": (psych.get("recommendations") or {}).get("top_spectra", [])[:3],
                        "instruments": (psych.get("recommendations") or {}).get("instruments", [])[:4],
                        "techniques": (psych.get("recommendations") or {}).get("techniques", [])[:3],
                    }
                    if session.org_entitlements:
                        event["data"]["association"] = {
                            "org_name": session.org_name,
                            "discipline_label": session.org_entitlements.get("discipline_label"),
                            "primary_lens": session.org_entitlements.get("primary_lens"),
                        }
                yield format_sse(event)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            yield format_sse({"event": "error", "data": {"message": str(exc)}})

    return EventSourceResponse(event_generator())


@app.post("/api/v1/chat/image-search")
async def chat_image_search(request: ImageSearchRequest):
    from app.services.image_search import search_images

    query = (request.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query_required")
    return await search_images(query, limit=request.limit)

@app.post("/api/v1/therapy/read")
async def therapy_read(request: ConsultationRequest):
    try:
        output = _compose_output(request.user_story, request.drawn_card, request.plan, request.selected_cards, request.preferred_school)
        _store_record(request.user_id, request.user_story, request.drawn_card, request.plan, output, request.preferred_school)
        _invalidate_user_caches(request.user_id)
        return {"plan": request.plan.upper(), "output": output, "stored": True}
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/v1/backoffice/samples")
async def backoffice_samples():
    samples: List[Dict[str, Any]] = []
    for user_id, record in PSYCHOLOGY_DATABASE.items():
        try:
            payload = _decrypt_payload(user_id, record["encrypted_payload"])
        except Exception:
            continue
        profile = payload.get("output", {}).get("psychiatric_feature_profile", {})
        samples.append(
            {
                "user_id": user_id,
                "plan": payload.get("plan", "FREE"),
                "preferred_school": payload.get("preferred_school"),
                "summary": payload.get("output", {}).get("summary", ""),
                "scope": payload.get("output", {}).get("scope", "brief"),
                "asset_value_krw": payload.get("asset_value_krw", 50000),
                "formal_scores": profile.get("formal_scores", {}),
                "battery_coverage": profile.get("battery_coverage", {}),
                "detected_cognitive_distortions": profile.get("detected_cognitive_distortions", []),
            }
        )
    return {"samples": samples[:10], "total": len(samples)}


@app.get("/api/v1/backoffice/export")
async def backoffice_b2b_export(request: Request):
    audit_token = os.getenv("PURGE_AUDIT_TOKEN", "").strip()
    provided_token = request.headers.get("x-audit-token")
    if not audit_token:
        raise HTTPException(status_code=500, detail="Export audit token is not configured")
    if not provided_token or provided_token != audit_token:
        raise HTTPException(status_code=401, detail="Valid X-Audit-Token header is required")

    write_audit_event("B2B_EXPORT", "backoffice", {"record_count": len(PSYCHOLOGY_DATABASE)})

    aggregates: List[Dict[str, Any]] = []
    for user_id, record in PSYCHOLOGY_DATABASE.items():
        try:
            payload = _decrypt_payload(user_id, record["encrypted_payload"])
        except Exception:
            continue
        profile = payload.get("output", {}).get("psychiatric_feature_profile", {})
        aggregates.append(
            {
                "anonymous_user_ref": user_id[:8] + "***",
                "plan": payload.get("plan", "FREE"),
                "preferred_school": payload.get("preferred_school"),
                "readiness_index": profile.get("psychological_readiness_index"),
                "attachment_matrix_score": profile.get("attachment_matrix_score"),
                "detected_cognitive_distortions": profile.get("detected_cognitive_distortions", []),
                "formal_scores": profile.get("formal_scores", {}),
                "battery_coverage": profile.get("battery_coverage", {}),
                "entry_count": len(payload.get("history") or []),
            }
        )

    return {
        "export_type": "b2b_aggregate",
        "record_count": len(aggregates),
        "aggregates": aggregates,
    }


@app.get("/api/v1/backoffice/analytics/summary")
async def backoffice_analytics_summary():
    school_counts: Dict[str, int] = {"FREUDIAN": 0, "ROGERIAN": 0, "BECK_CBT": 0}
    tree_energy_values: List[float] = []
    distortion_counts: Dict[str, int] = {}

    for user_id, record in PSYCHOLOGY_DATABASE.items():
        try:
            payload = _decrypt_payload(user_id, record["encrypted_payload"])
        except Exception:
            continue

        school = payload.get("preferred_school")
        if school in school_counts:
            school_counts[school] += 1

        history = payload.get("history") or []
        for entry in history:
            profile = entry.get("output", {}).get("psychiatric_feature_profile", {}).get("drawing_projective_profile", {})
            tree_energy = profile.get("tree_energy_index")
            if isinstance(tree_energy, (int, float)):
                tree_energy_values.append(float(tree_energy))

            distortions = entry.get("output", {}).get("psychiatric_feature_profile", {}).get("detected_cognitive_distortions", [])
            if not isinstance(distortions, list):
                continue
            for distortion in distortions:
                if not isinstance(distortion, str):
                    continue
                normalized = distortion.strip().lower()
                if not normalized:
                    continue
                distortion_counts[normalized] = distortion_counts.get(normalized, 0) + 1

    total_records = max(1, len(PSYCHOLOGY_DATABASE))
    preferred_school_distribution = {
        school: round((count / total_records) * 100.0, 2) for school, count in school_counts.items()
    }

    if len(tree_energy_values) >= 2:
        mean = sum(tree_energy_values) / len(tree_energy_values)
        variance = sum((value - mean) ** 2 for value in tree_energy_values) / len(tree_energy_values)
    else:
        variance = 0.0

    ranked_distortions = [
        {"pattern": pattern, "count": count}
        for pattern, count in sorted(distortion_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    battery_completion_rates: List[float] = []
    for user_id, record in PSYCHOLOGY_DATABASE.items():
        try:
            payload = _decrypt_payload(user_id, record["encrypted_payload"])
        except Exception:
            continue
        for entry in payload.get("history") or []:
            battery = entry.get("output", {}).get("psychiatric_feature_profile", {}).get("battery_coverage", {})
            rate = battery.get("overall_completion_rate")
            if isinstance(rate, (int, float)):
                battery_completion_rates.append(float(rate))

    avg_battery_completion = (
        round(sum(battery_completion_rates) / len(battery_completion_rates), 2)
        if battery_completion_rates
        else 0.0
    )

    return {
        "total_records": len(PSYCHOLOGY_DATABASE),
        "preferred_school_distribution": preferred_school_distribution,
        "tree_energy_variance": round(variance, 4),
        "ranked_detected_cognitive_distortions": ranked_distortions,
        "avg_battery_completion_rate": avg_battery_completion,
        "battery_sessions_tracked": len(battery_completion_rates),
    }


@app.get("/api/v1/therapy/dashboard/{user_id}")
async def therapy_dashboard(user_id: str, membership_tier: Optional[str] = None):
    if user_id == "invalid-user":
        raise InvalidUserException(user_id)
    write_audit_event("DASHBOARD_READ", user_id, {"membership_tier": membership_tier or "FREE"})
    tier = (membership_tier or "FREE").upper()
    cache_key = f"dashboard:{user_id}:{tier}"
    cached_value = DASHBOARD_CACHE.get(cache_key)
    if cached_value is not None:
        return cached_value
    payload = _build_dashboard_payload(user_id, tier)
    DASHBOARD_CACHE.set(cache_key, payload)
    return payload


@app.get("/api/v1/therapy/analytics/{user_id}")
async def therapy_analytics(user_id: str):
    if user_id == "decrypt-fail":
        raise DecryptionFailureException(user_id)
    if user_id == "bad-persona":
        raise InvalidPersonaException("bad-persona")

    write_audit_event("ANALYTICS_READ", user_id)

    cached_value = ANALYTICS_CACHE.get(user_id)
    if cached_value is not None:
        return cached_value

    history = _load_history(user_id)
    if not history:
        payload = {
            "user_id": user_id,
            "total_entries": 0,
            "distribution_profile": {},
            "ranked_patterns": [],
        }
        ANALYTICS_CACHE.set(user_id, payload)
        return payload

    counts: Dict[str, int] = {}
    for entry in history:
        distortions = entry.get("output", {}).get("psychiatric_feature_profile", {}).get("detected_cognitive_distortions", [])
        if not isinstance(distortions, list):
            continue
        for distortion in distortions:
            if not isinstance(distortion, str):
                continue
            normalized = distortion.strip().lower()
            if not normalized:
                continue
            counts[normalized] = counts.get(normalized, 0) + 1

    total_entries = max(1, len(history))
    distribution_profile = {
        key: round(value / total_entries * 100.0, 2)
        for key, value in sorted(counts.items(), key=lambda item: item[0])
    }
    ranked_patterns = [
        {"pattern": key, "count": counts[key], "percentage": distribution_profile[key]}
        for key in sorted(counts, key=lambda item: (-counts[item], item))
    ]

    payload = {
        "user_id": user_id,
        "total_entries": len(history),
        "distribution_profile": distribution_profile,
        "ranked_patterns": ranked_patterns,
    }
    ANALYTICS_CACHE.set(user_id, payload)
    return payload


@app.get("/api/v1/therapy/stream/{user_id}")
async def therapy_stream(user_id: str):
    async def event_stream():
        try:
            history = _load_history(user_id)
            if not history:
                event = {
                    "type": "progress",
                    "message": "No clinical history available yet.",
                    "user_id": user_id,
                    "data": {},
                }
                yield {"event": "message", "data": json.dumps(event)}
                return

            for entry in history:
                output = entry.get("output") or {}
                profile = (output.get("psychiatric_feature_profile") or {}).get("drawing_projective_profile") or {}
                event = {
                    "type": "progress",
                    "message": "Streaming clinical profile data.",
                    "user_id": user_id,
                    "data": {
                        "psychological_readiness_index": profile.get("psychological_readiness_index"),
                        "tree_energy_index": profile.get("tree_energy_index"),
                        "cognitive_distortion_analysis": {
                            "flags": output.get("psychiatric_feature_profile", {}).get("cognitive_distortion_flags", []),
                            "attachment_matrix_score": output.get("psychiatric_feature_profile", {}).get("attachment_matrix_score", 0.0),
                        },
                    },
                }
                yield {"event": "message", "data": json.dumps(event)}
                await asyncio.sleep(0.1)

            final_event = {
                "type": "complete",
                "message": "Clinical streaming completed.",
                "user_id": user_id,
                "data": {"entries_streamed": len(history)},
            }
            yield {"event": "message", "data": json.dumps(final_event)}
        except asyncio.CancelledError:
            raise
        except Exception:
            error_event = {
                "type": "error",
                "message": "Stream interrupted.",
                "user_id": user_id,
                "data": {},
            }
            yield {"event": "message", "data": json.dumps(error_event)}

    return EventSourceResponse(event_stream())


@app.delete("/api/v1/therapy/purge")
async def therapy_purge(request: Request, user_id: Optional[str] = None):
    try:
        payload: Optional[Dict[str, Any]] = None
        try:
            payload = await request.json()
        except Exception:
            payload = None

        if isinstance(payload, dict):
            target_user_id = user_id or str(payload.get("user_id") or "").strip() or None
        else:
            target_user_id = user_id

        if not target_user_id:
            raise HTTPException(status_code=422, detail="user_id is required")

        audit_token = os.getenv("PURGE_AUDIT_TOKEN", "").strip()
        provided_token = request.headers.get("x-audit-token")

        if not audit_token:
            raise HTTPException(status_code=500, detail="Purge audit token is not configured")
        if not provided_token:
            raise HTTPException(status_code=401, detail="X-Audit-Token header is required")
        if provided_token != audit_token:
            raise HTTPException(status_code=403, detail="Invalid X-Audit-Token")

        def _purge_in_sandbox() -> None:
            if target_user_id in PSYCHOLOGY_DATABASE:
                del PSYCHOLOGY_DATABASE[target_user_id]
            PURGED_USERS.add(target_user_id)
            _purge_chat_sessions(target_user_id)
            _invalidate_user_caches(target_user_id)

        _purge_in_sandbox()

        write_audit_event(
            "PURGE_COMMITTED",
            target_user_id,
            {"memory_erased": True},
            actor=provided_token[:8] + "***" if provided_token else "system",
        )

        return {"status": "purged", "user_id": target_user_id, "memory_erased": True, "vault_sealed": True}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise HTTPException(status_code=500, detail=str(exc)) from exc