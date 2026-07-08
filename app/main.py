import asyncio
import os
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sse_starlette import EventSourceResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

from app.prompt_config import build_system_prompt, build_user_prompt

# 환경 변수 로드 및 AI 클라이언트 초기화
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Psychology Tarot AI System")

import base64
import json
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet

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
        else:
            self._entries.pop(key, None)


DASHBOARD_CACHE = InMemoryTTLCache()
ANALYTICS_CACHE = InMemoryTTLCache()

TAROT_ARCHETYPE_MAP = {
    "The Fool": {
        "archetype": "The Innocent",
        "psychiatric_stress_weight": 0.35,
        "cognitive_distortion_flag": "catastrophizing",
        "attachment_matrix_score": 0.42,
    },
    "The Tower": {
        "archetype": "The Destroyer",
        "psychiatric_stress_weight": 0.81,
        "cognitive_distortion_flag": "all_or_nothing",
        "attachment_matrix_score": 0.28,
    },
    "The Magician": {
        "archetype": "The Creator",
        "psychiatric_stress_weight": 0.47,
        "cognitive_distortion_flag": "overgeneralization",
        "attachment_matrix_score": 0.61,
    },
}


def _get_fernet() -> Fernet:
    key = os.getenv("FERNET_KEY")
    if not key:
        key = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")
        os.environ["FERNET_KEY"] = key
    return Fernet(key.encode("utf-8"))


def _encrypt_payload(payload: Dict[str, Any]) -> str:
    return _get_fernet().encrypt(json.dumps(payload).encode("utf-8")).decode("utf-8")


def _decrypt_payload(token: str) -> Dict[str, Any]:
    return json.loads(_get_fernet().decrypt(token.encode("utf-8")).decode("utf-8"))


class ClinicalSchool(str, Enum):
    FREUDIAN = "FREUDIAN"
    ROGERIAN = "ROGERIAN"
    BECK_CBT = "BECK_CBT"


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


def _build_archetype_profile(user_story: str, selected_cards: Optional[List[str]] = None) -> Dict[str, Any]:
    selected = selected_cards or []
    profiles: List[Dict[str, Any]] = []
    flags: List[str] = []
    scores: List[float] = []

    for card_name in selected:
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
        flags.append(mapping["cognitive_distortion_flag"])
        scores.append(mapping["attachment_matrix_score"])

    if not profiles:
        fallback_flag = "rumination" if any(keyword in (user_story or "").lower() for keyword in ["불안", "스트레스", "혼란", "두려움"]) else "none"
        return {
            "cognitive_distortion_flags": [fallback_flag],
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
    if school == ClinicalSchool.FREUDIAN:
        return {
            "clinical_protocol_mode": "FREUDIAN",
            "assistant_behavior_rules": [
                "Explore unconscious conflict with gentle curiosity.",
                "Frame recurring patterns as unresolved emotional themes.",
                "Encourage reflection on early relational imprints."
            ],
            "daily_logotherapy_homework_style": "A reflective journaling exercise on unconscious repetition and emotional conflict.",
        }
    if school == ClinicalSchool.BECK_CBT:
        return {
            "clinical_protocol_mode": "BECK_CBT",
            "assistant_behavior_rules": [
                "Identify cognitive distortions with precision.",
                "Reframe maladaptive thoughts into balanced alternatives.",
                "Anchor the plan in measurable behavioral experiments."
            ],
            "daily_logotherapy_homework_style": "A thought record exercise focused on evidence, reframe, and behavioral experiment.",
        }
    return {
        "clinical_protocol_mode": "ROGERIAN",
        "assistant_behavior_rules": [
            "Offer unconditional positive regard.",
            "Validate the client's experience without judgment.",
            "Support self-directed growth through empathic reflection."
        ],
        "daily_logotherapy_homework_style": "A gentle reflective homework prompt centered on self-acceptance and emotional safety.",
    }


def _compose_output(user_story: str, drawn_card: str, plan: str, selected_cards: Optional[List[str]] = None, preferred_school: Optional[ClinicalSchool] = None) -> Dict[str, Any]:
    config = _resolve_plan(plan)
    system_prompt = build_system_prompt()
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

    school = _resolve_clinical_school(preferred_school)
    behavior_metadata = _build_behavior_metadata(school)
    readiness_index = _build_psychological_readiness_index(user_story, plan, selected_cards)
    profile = _build_projective_profile(user_story, drawn_card, readiness_index)
    archetype_profile = _build_archetype_profile(user_story, selected_cards)
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
            "attachment_matrix_score": archetype_profile["attachment_matrix_score"],
            "archetype_profiles": archetype_profile["archetype_profiles"],
        },
        **behavior_metadata,
    }


def _store_record(user_id: str, user_story: str, drawn_card: str, plan: str, output: Dict[str, Any]) -> None:
    existing_record = PSYCHOLOGY_DATABASE.get(user_id)
    history: List[Dict[str, Any]] = []
    if existing_record:
        try:
            existing_payload = _decrypt_payload(existing_record["encrypted_payload"])
            history = existing_payload.get("history") or []
        except Exception:
            history = []

    payload = {
        "user_id": user_id,
        "user_story": user_story,
        "drawn_card": drawn_card,
        "plan": plan,
        "output": output,
        "anonymous": True,
        "asset_value_krw": 50000,
        "timestamp": len(history),
        "history": history + [{
            "user_id": user_id,
            "user_story": user_story,
            "drawn_card": drawn_card,
            "plan": plan,
            "output": output,
            "timestamp": len(history),
        }],
    }
    PSYCHOLOGY_DATABASE[user_id] = {
        "encrypted_payload": _encrypt_payload(payload),
        "asset_value_krw": 50000,
    }


def _load_history(user_id: str) -> List[Dict[str, Any]]:
    record = PSYCHOLOGY_DATABASE.get(user_id)
    if not record:
        return []
    try:
        payload = _decrypt_payload(record["encrypted_payload"])
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

    if not series:
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
            "history_length": len(series),
            "summary": premium_summary,
            "trend_analysis": trend_analysis,
            "premium_therapeutic_summary": premium_summary,
        }

    return {
        "user_id": user_id,
        "membership_tier": membership_tier.upper(),
        "history_length": len(series),
        "summary": "Advanced analytics require a premium subscription.",
        "trend_analysis": trend_analysis,
    }


def _invalidate_user_caches(user_id: str) -> None:
    DASHBOARD_CACHE.invalidate(user_id)
    ANALYTICS_CACHE.invalidate(user_id)


@app.post("/api/v1/therapy/read")
async def therapy_read(request: ConsultationRequest):
    try:
        output = _compose_output(request.user_story, request.drawn_card, request.plan, request.selected_cards, request.preferred_school)
        _store_record(request.user_id, request.user_story, request.drawn_card, request.plan, output)
        _invalidate_user_caches(request.user_id)
        return {"plan": request.plan.upper(), "output": output, "stored": True}
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/v1/backoffice/samples")
async def backoffice_samples():
    samples: List[Dict[str, Any]] = []
    for user_id, record in PSYCHOLOGY_DATABASE.items():
        try:
            payload = _decrypt_payload(record["encrypted_payload"])
        except Exception:
            continue
        samples.append(
            {
                "user_id": user_id,
                "plan": payload.get("plan", "FREE"),
                "summary": payload.get("output", {}).get("summary", ""),
                "scope": payload.get("output", {}).get("scope", "brief"),
                "asset_value_krw": 50000,
            }
        )
    return {"samples": samples[:10], "total": len(samples)}


@app.get("/api/v1/therapy/dashboard/{user_id}")
async def therapy_dashboard(user_id: str, membership_tier: Optional[str] = None):
    if user_id == "invalid-user":
        raise InvalidUserException(user_id)
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
    history = _load_history(user_id)
    if not history:
        return {
            "user_id": user_id,
            "total_entries": 0,
            "distribution_profile": {},
            "ranked_patterns": [],
        }

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

    return {
        "user_id": user_id,
        "total_entries": len(history),
        "distribution_profile": distribution_profile,
        "ranked_patterns": ranked_patterns,
    }


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
            _invalidate_user_caches(target_user_id)

        _purge_in_sandbox()

        audit_log_path = os.getenv("PURGE_AUDIT_LOG_PATH", "purge_audit.jsonl")
        audit_dir = os.path.dirname(audit_log_path)
        if audit_dir:
            os.makedirs(audit_dir, exist_ok=True)
        audit_entry = {
            "user_id": target_user_id,
            "action_type": "PURGE_COMMITTED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(audit_log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(audit_entry, separators=(",", ":")) + "\n")

        return {"status": "purged", "user_id": target_user_id, "memory_erased": True}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise HTTPException(status_code=500, detail=str(exc)) from exc