import os
from fastapi import FastAPI, HTTPException
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


class DrawingProjectiveProfile(BaseModel):
    structural_sign: str
    house_interpreted_code: str
    tree_energy_index: float
    person_relational_tag: str


class PsychiatricFeatureProfile(BaseModel):
    drawing_projective_profile: DrawingProjectiveProfile


class ConsultationRequest(BaseModel):
    user_id: str = "anonymous"
    user_story: str
    drawn_card: str
    plan: str = "FREE"


class PurgeRequest(BaseModel):
    user_id: str


def _resolve_plan(plan: str) -> Dict[str, Any]:
    normalized = (plan or "FREE").upper()
    return PLAN_RULES.get(normalized, PLAN_RULES["FREE"])


def _build_fallback_analysis(user_story: str, drawn_card: str, plan: str) -> str:
    return (
        f"{user_story}\n"
        f"카드 '{drawn_card}'는 현재 불안과 성찰의 시점으로 해석됩니다.\n"
        f"{plan} 등급 기준으로는 짧고 실천 가능한 CBT 중심 접근을 권장합니다."
    )


def _build_projective_profile(user_story: str, drawn_card: str) -> Dict[str, Any]:
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
    }


def _compose_output(user_story: str, drawn_card: str, plan: str) -> Dict[str, Any]:
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

    profile = _build_projective_profile(user_story, drawn_card)
    return {
        "summary": analysis,
        "scope": config["scope"],
        "detail_level": config["detail_level"],
        "actions": actions,
        "asset_value_krw": 50000,
        "safety_note": "위기 상황 시 전문가 또는 응급 지원을 권장합니다.",
        "psychiatric_feature_profile": {
            "drawing_projective_profile": profile,
        },
    }


def _store_record(user_id: str, user_story: str, drawn_card: str, plan: str, output: Dict[str, Any]) -> None:
    payload = {
        "user_id": user_id,
        "user_story": user_story,
        "drawn_card": drawn_card,
        "plan": plan,
        "output": output,
        "anonymous": True,
        "asset_value_krw": 50000,
    }
    PSYCHOLOGY_DATABASE[user_id] = {
        "encrypted_payload": _encrypt_payload(payload),
        "asset_value_krw": 50000,
    }


@app.post("/api/v1/therapy/read")
async def therapy_read(request: ConsultationRequest):
    try:
        output = _compose_output(request.user_story, request.drawn_card, request.plan)
        _store_record(request.user_id, request.user_story, request.drawn_card, request.plan, output)
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


@app.delete("/api/v1/therapy/purge")
async def therapy_purge(request: PurgeRequest):
    try:
        if request.user_id in PSYCHOLOGY_DATABASE:
            del PSYCHOLOGY_DATABASE[request.user_id]
        PURGED_USERS.add(request.user_id)
        return {"status": "purged", "user_id": request.user_id, "memory_erased": True}
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise HTTPException(status_code=500, detail=str(exc)) from exc