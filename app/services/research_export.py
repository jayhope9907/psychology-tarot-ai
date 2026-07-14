"""연구·IRB형 비식별 export · 정부지원/특허용 KPI (비진단)."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.db.database import get_connection, init_db
from app.services.legal_compliance import SERVICE_NAME, SERVICE_SCOPE_SUMMARY

RESEARCH_SCHEMA_VERSION = "1.0.0"
RESEARCH_PURPOSE = (
    "디지털 마음 웰니스·교육 UX 연구 및 학회 수련 도구 평가. "
    "진단 성능·치료 효과 검증이 목적이 아닙니다."
)

INVENTION_IDS = [
    {
        "id": "INV-01",
        "title_ko": "피로·단계 인식형 다도구 상담 오케스트레이터",
        "title_en": "Fatigue- and phase-aware multi-instrument counseling orchestrator",
        "claim_sketch": (
            "세션 피로·상담 단계·도구 이력에 따라 스크리닝 주입·대화·워밍업을 "
            "선택하는 방법 및 시스템"
        ),
        "modules": ["orchestrator", "fatigue_manager", "counseling_phase", "assessment_selector"],
    },
    {
        "id": "INV-02",
        "title_ko": "학회·수련 라이선스 권한 기반 AI 에이전트 라우팅",
        "title_en": "Discipline-entitlement-conditioned association AI agent routing",
        "claim_sketch": (
            "학회·수련 유형별 허용 검사·기능 플래그에 따라 에이전트 지시문·도구 집합을 "
            "조건부 구성하는 시스템"
        ),
        "modules": ["association_licensing", "association_agent", "license_store"],
    },
    {
        "id": "INV-03",
        "title_ko": "라이선스 발급 시 종단 데모 사례 백데이팅 시드",
        "title_en": "License-provision longitudinal demo-case timeline seeding",
        "claim_sketch": (
            "라이선스 프로비저닝과 연동하여 수련용 데모 사례·타임라인을 "
            "백데이트 시드하는 온보딩 방법"
        ),
        "modules": ["license_case_seed", "psych_timeline", "association_agent"],
    },
    {
        "id": "INV-04",
        "title_ko": "상징 모달리티(타로·픽토·사진)↔구조화 웰니스 대화 브리지",
        "title_en": "Symbolic modality bridge into structured wellness dialogue",
        "claim_sketch": (
            "타로·픽토·이미지 검색/비전 입력을 비진단 제약 하에서 "
            "구조화 상담 대화로 연결하는 멀티모달 방법"
        ),
        "modules": ["tarot_bridge", "image_search", "picto_vocabulary", "chat_stream"],
    },
    {
        "id": "INV-05",
        "title_ko": "투영 표현 배터리·종단 psych timeline 통합 파이프라인",
        "title_en": "Projective battery with longitudinal psych-timeline pipeline",
        "claim_sketch": (
            "그림·이야기 표현 배터리와 종단 이벤트 저장·재구성을 "
            "라이선스 권한으로 필터링하는 웰니스 데이터 파이프라인"
        ),
        "modules": ["projective_battery", "picture_assessment", "psych_timeline", "clinical_catalog"],
    },
    {
        "id": "INV-06",
        "title_ko": "사용자별 진화형 AI 상담 지문(ALG) 및 학파 사전 편향",
        "title_en": "Per-user evolving counselor agent fingerprint with school priors",
        "claim_sketch": (
            "세션 정량 지표·학파·왜곡·주제 히스토그램을 EMA·패턴으로 누적하고, "
            "고유 ALG 식별자와 프롬프트 바인딩·라우팅 편향을 생성하는 방법"
        ),
        "modules": ["user_agent_algorithm", "prompt_binding", "persona_router", "psych_timeline"],
    },
    {
        "id": "INV-07",
        "title_ko": "물질·행동 중독 도메인 온톨로지 기반 이론·기법 라우팅",
        "title_en": "Substance/behavioral-addiction ontology routing of theories and techniques",
        "claim_sketch": (
            "중독 웰니스 온톨로지(이론·기법·스크리너·위기핸드오프)에 따라 "
            "메시지 키워드를 임상 학파·기법 카드로 매핑하고 비의료 제약을 강제하는 시스템"
        ),
        "modules": ["addiction_theories", "dsm5_framework", "persona_router", "assessment_selector"],
    },
    {
        "id": "INV-08",
        "title_ko": "상담 응답 유사도 기반 반반복 오케스트레이션",
        "title_en": "Similarity-gated anti-repetition counseling response orchestration",
        "claim_sketch": (
            "직전 어시스턴트 발화와의 n-gram·종결문 유사도를 검사해 "
            "중복 시 변형 응답·프롬프트 금지 지시로 교체하는 대화 품질 제어 방법"
        ),
        "modules": ["chat_stream", "orchestrator", "counsel_offline"],
    },
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _anon_ref(user_id: str) -> str:
    digest = hashlib.sha256(f"research:{user_id}".encode("utf-8")).hexdigest()
    return f"anon-{digest[:12]}"


def research_consent_document() -> Dict[str, Any]:
    return {
        "document_id": "research-consent-v1",
        "service_name": SERVICE_NAME,
        "schema_version": RESEARCH_SCHEMA_VERSION,
        "purpose": RESEARCH_PURPOSE,
        "service_scope": SERVICE_SCOPE_SUMMARY,
        "data_categories": [
            "비식별 세션·턴 메타데이터",
            "스크리닝·표현 도구 완료/피로 지표 (원문 대화 제외 기본)",
            "위기 핸드오프 발생 여부 (내용 제외)",
            "학회 라이선스 유형·좌석 이용 (기관 단위)",
        ],
        "excluded_by_default": [
            "대화 전문(free text)",
            "첨부 사진·생체 식별 가능 이미지",
            "실명·연락처·정확한 위치",
            "진단명·처방 정보 (본 서비스는 생성하지 않음)",
        ],
        "retention": "연구 동의 철회 또는 목적 달성 시까지. 기관 계약에 따름.",
        "rights": [
            "언제든지 연구 동의 철회 가능",
            "개인정보 삭제(purge) 요청 가능",
            "비식별 export만 기본 제공",
        ],
        "non_claims": [
            "본 연구 데이터는 진단·치료 효과 입증용이 아닙니다.",
            "의료기기·임상시험 결과로 해석하지 않습니다.",
            "정부지원·특허 자료의 KPI는 참여·안전·완료율 중심입니다.",
        ],
        "acknowledgments": [
            "연구 목적·비식별 처리·비진단 범위를 이해했습니다.",
            "원문 대화는 기본 export에 포함되지 않음을 이해했습니다.",
            "의료·정신과 진료를 대체하지 않음을 확인했습니다.",
        ],
    }


def list_inventions() -> List[Dict[str, Any]]:
    return list(INVENTION_IDS)


def build_codebook() -> Dict[str, Any]:
    return {
        "schema_version": RESEARCH_SCHEMA_VERSION,
        "fields": [
            {"name": "anonymous_user_ref", "type": "string", "desc": "SHA256 기반 비식별 참조키"},
            {"name": "session_count", "type": "int", "desc": "저장된 세션 수"},
            {"name": "turn_count_total", "type": "int", "desc": "누적 대화 턴"},
            {"name": "assessment_offers", "type": "int", "desc": "스크리닝 제안 횟수"},
            {"name": "assessment_completions", "type": "int", "desc": "스크리닝 응답 횟수"},
            {"name": "crisis_handoff_flag", "type": "bool", "desc": "위기 안내 발생 여부(내용 없음)"},
            {"name": "fatigue_blocks", "type": "int", "desc": "피로로 검사 주입이 억제된 횟수"},
            {"name": "discipline_id", "type": "string|null", "desc": "학회/수련 렌즈 ID"},
            {"name": "has_timeline_events", "type": "bool", "desc": "종단 이벤트 존재 여부"},
            {"name": "timeline_event_count", "type": "int", "desc": "종단 이벤트 수"},
        ],
        "primary_endpoints_non_efficacy": [
            "session_completion_proxy",
            "crisis_handoff_rate",
            "assessment_fatigue_block_rate",
            "association_seat_utilization",
            "offline_capable_surfaces",
        ],
    }


def _session_aggregates(limit: int = 500) -> List[Dict[str, Any]]:
    import json

    init_db()
    conn = get_connection()
    rows: List[Dict[str, Any]] = []
    try:
        session_rows = conn.execute(
            """
            SELECT session_id, user_id, state_json, updated_at
            FROM session_snapshots
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        for row in session_rows:
            user_id = row["user_id"]
            try:
                state = json.loads(row["state_json"] or "{}")
            except Exception:
                state = {}
            timeline_count = 0
            try:
                timeline_count = conn.execute(
                    "SELECT COUNT(*) AS c FROM psych_timeline_events WHERE user_id = ?",
                    (user_id,),
                ).fetchone()["c"]
            except Exception:
                timeline_count = 0
            entitlements = state.get("org_entitlements") or {}
            rows.append(
                {
                    "anonymous_user_ref": _anon_ref(user_id),
                    "session_id_hash": hashlib.sha256(str(row["session_id"]).encode()).hexdigest()[:16],
                    "turn_count": int(state.get("turn_count") or 0),
                    "counseling_phase": state.get("counseling_phase"),
                    "preferred_school": state.get("preferred_school"),
                    "plan": state.get("plan"),
                    "discipline_id": entitlements.get("discipline_id"),
                    "has_timeline_events": timeline_count > 0,
                    "timeline_event_count": int(timeline_count or 0),
                    "updated_at_day": str(row["updated_at"] or "")[:10],
                }
            )
    except Exception:
        rows = []
    finally:
        conn.close()
    return rows


def _license_utilization() -> List[Dict[str, Any]]:
    init_db()
    conn = get_connection()
    out: List[Dict[str, Any]] = []
    try:
        rows = conn.execute(
            """
            SELECT o.discipline_id, o.tier_id, o.org_name,
                   l.seats_total, l.seats_used, l.status
            FROM organizations o
            LEFT JOIN organization_licenses l ON l.org_id = o.org_id
            """
        ).fetchall()
        for row in rows:
            total = int(row["seats_total"] or 0)
            used = int(row["seats_used"] or 0)
            out.append(
                {
                    "discipline_id": row["discipline_id"],
                    "tier_id": row["tier_id"],
                    "org_name_redacted": (row["org_name"] or "")[:24],
                    "seats_total": total,
                    "seats_used": used,
                    "utilization_rate": round(used / total, 4) if total else 0.0,
                    "status": row["status"],
                }
            )
    except Exception:
        out = []
    finally:
        conn.close()
    return out


def build_research_export(
    *,
    include_sessions: bool = True,
    limit: int = 500,
    research_consent: bool = False,
) -> Dict[str, Any]:
    if not research_consent:
        return {
            "ok": False,
            "error": "research_consent_required",
            "message_ko": "연구 동의가 필요합니다. /api/v1/research/consent 문서를 확인하세요.",
            "consent": research_consent_document(),
        }

    sessions = _session_aggregates(limit=limit) if include_sessions else []
    licenses = _license_utilization()
    turn_total = sum(s.get("turn_count", 0) for s in sessions)
    crisis_proxy = 0  # content-free; filled by grant KPIs from audit if available

    return {
        "ok": True,
        "export_type": "research_deidentified_v1",
        "schema_version": RESEARCH_SCHEMA_VERSION,
        "exported_at": _utc_now(),
        "purpose": RESEARCH_PURPOSE,
        "service_scope": SERVICE_SCOPE_SUMMARY,
        "codebook": build_codebook(),
        "records": {
            "sessions": sessions,
            "license_utilization": licenses,
        },
        "summary": {
            "session_rows": len(sessions),
            "turn_count_total": turn_total,
            "license_orgs": len(licenses),
            "crisis_handoff_flag_note": "원문 없이 audit KPI로 별도 집계",
            "crisis_proxy_placeholder": crisis_proxy,
        },
        "non_claims": research_consent_document()["non_claims"],
    }


def build_grant_kpis() -> Dict[str, Any]:
    """정부지원 평가용 비효능(non-efficacy) KPI."""
    sessions = _session_aggregates(limit=1000)
    licenses = _license_utilization()
    turn_total = sum(s.get("turn_count", 0) for s in sessions)
    with_timeline = sum(1 for s in sessions if s.get("has_timeline_events"))
    avg_turns = (turn_total / len(sessions)) if sessions else 0.0
    util_rates = [x["utilization_rate"] for x in licenses if x.get("seats_total")]
    avg_util = sum(util_rates) / len(util_rates) if util_rates else 0.0

    return {
        "framework": "non_efficacy_engagement_safety",
        "as_of": _utc_now(),
        "disclaimer_ko": (
            "본 KPI는 참여·안전·도구 이용 지표이며, "
            "증상 호전·치료 효과·진단 정확도를 나타내지 않습니다."
        ),
        "kpis": {
            "active_session_rows": len(sessions),
            "mean_turns_per_session": round(avg_turns, 2),
            "timeline_coverage_rate": round(with_timeline / len(sessions), 4) if sessions else 0.0,
            "association_mean_seat_utilization": round(avg_util, 4),
            "association_org_count": len(licenses),
            "invention_count": len(INVENTION_IDS),
            "offline_surfaces": ["picto", "tarot_bundle", "counsel_offline"],
            "trainee_license_tracks": [
                "clinical_psych_trainee",
                "mh_social_work_trainee",
            ],
            "multimodal_inputs": ["text", "photo_vision", "image_search", "tarot", "picto", "drawing"],
        },
        "grant_alignment": {
            "mss_startup": "디지털 웰니스·교육 SW · B2B 학회/수련 라이선스",
            "msit_rd": "멀티모달·오케스트레이션·종단 UX 파이프라인 R&D",
            "mohw_digital": "정신건강 위기 연계·비진단 스크리닝 교육 보조 (의료기기 아님)",
            "tips_style": "차별화 기술(오케스트레이터·라이선스 에이전트·시드) + B2B 트랙션",
        },
        "inventions": INVENTION_IDS,
    }


def build_innovation_catalog() -> Dict[str, Any]:
    return {
        "product_name": SERVICE_NAME,
        "tagline_ko": "학회·수련 렌즈에 맞춘 AI 마음 웰니스·교육 플랫폼",
        "service_scope": SERVICE_SCOPE_SUMMARY,
        "inventions": INVENTION_IDS,
        "research": {
            "consent": "/api/v1/research/consent",
            "export": "/api/v1/research/export",
            "codebook": "/api/v1/research/codebook",
            "kpis": "/api/v1/research/grant-kpis",
        },
        "docs": {
            "invention_disclosure": "/docs/ip/invention-disclosure.md",
            "grant_brief": "/docs/grant/korea-grant-brief.md",
            "readme": "/",
            "innovation_ui": "/innovation",
        },
        "demo_licenses": [
            "MSHT-COUNSEL-DEMO-2026",
            "MSHT-PSYCH-DEMO-2026",
            "MSHT-PSYCHIATRY-DEMO-2026",
            "MSHT-CLINICAL-DEMO-2026",
            "MSHT-MHSW-DEMO-2026",
        ],
    }
