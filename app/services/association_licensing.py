"""학회·협회 B2B 라이선스 — 학문별 초점·구독·권한."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Set

from app.models.association import AssociationDiscipline, LicenseTier

# ── 학회 유형별 핵심 렌즈 ─────────────────────────────────────────────
DISCIPLINE_PROFILES: Dict[str, Dict[str, Any]] = {
    AssociationDiscipline.COUNSELING.value: {
        "discipline_id": AssociationDiscipline.COUNSELING.value,
        "label_ko": "상담학회 · 상담심리",
        "tagline": "사례 중심 · 관계·공정 · 상담 프로세스",
        "primary_lens": "사례(Case) · 개입(Intervention) · 숙제(Homework)",
        "what_we_optimize": [
            "라포 → 개념화 → 개입 → 종결 5단계 상담 흐름",
            "19개 상담 이론·학파 (로저스, 벡, IPT, DBT, 가족치료 등)",
            "타로·투사를 은유·거울로 활용 (깊은 무의식 해석 최소)",
            "SCT·애착·행동 회피 등 대화형 탐색",
        ],
        "what_we_de_emphasize": [
            "질병명·정신병 진단 라벨링",
            "약물·처방 관련 안내",
            "DSM 장애군 단정",
        ],
        "hero_stat": "사례 개념화 · 관계 패턴",
        "color": "#3d6b5a",
        "icon": "🤝",
        "allowed_instruments": [
            "sct",
            "attachment_ecr",
            "micro_emotion",
            "htp",
            "behavioral",
            "cbt_thought",
            "psychodynamic",
            "tarot_reflect",
        ],
        "feature_flags": {
            "counseling_theories_full": True,
            "counseling_phases": True,
            "homework_packages": True,
            "tarot_bridge": True,
            "assessment_packages": True,
            "dsm5_catalog": False,
            "clinical_insight_risk": False,
            "psych_timeline": True,
            "b2b_export": False,
            "white_label": False,
        },
        "legal_framing_ko": (
            "상담학회 라이선스는 **AI 웰니스·자기성찰·상담 교육 보조**용입니다. "
            "면허 상담·임상심리치료·진단을 대체하지 않으며, 슈퍼바이저 교육·사례 토론 보조 도구로 사용합니다."
        ),
    },
    AssociationDiscipline.PSYCHOLOGY.value: {
        "discipline_id": AssociationDiscipline.PSYCHOLOGY.value,
        "label_ko": "심리학회 · 임상·일반심리",
        "tagline": "측정·데이터 · 종단 추적 · 심리검사 배터리",
        "primary_lens": "심리측정(Psychometrics) · 프로파일 · 연구 데이터",
        "what_we_optimize": [
            "PHQ-9·GAD-7·RSES 등 표준화 스크리닝 (웰니스 프레이밍)",
            "5축 기분·psych timeline 백필·종단 프로파일",
            "검사 패키지·배터리 커버리지·학회 교육용 리포트",
            "SCT·투사·애착 등 서사+수치 혼합",
        ],
        "what_we_de_emphasize": [
            "정신과적 처방·응급 의료 개입",
            "단일 진단명 확정",
        ],
        "hero_stat": "심리측정 · 종단 데이터",
        "color": "#3182F6",
        "icon": "📊",
        "allowed_instruments": [
            "phq9",
            "gad7",
            "rses",
            "pss",
            "isi",
            "sct",
            "attachment_ecr",
            "micro_emotion",
            "htp",
            "cbt_thought",
            "behavioral",
        ],
        "feature_flags": {
            "counseling_theories_full": True,
            "counseling_phases": True,
            "homework_packages": True,
            "tarot_bridge": True,
            "assessment_packages": True,
            "dsm5_catalog": True,
            "clinical_insight_risk": True,
            "psych_timeline": True,
            "b2b_export": True,
            "white_label": False,
        },
        "legal_framing_ko": (
            "심리학회 라이선스는 **심리측정·연구·교육용 스크리닝**입니다. "
            "임상심리사·연구倫리 지침에 따른 비진단·참고용 데이터이며, "
            "공식 심리검사 실시 자격과는 별개입니다."
        ),
    },
    AssociationDiscipline.PSYCHIATRY.value: {
        "discipline_id": AssociationDiscipline.PSYCHIATRY.value,
        "label_ko": "정신의학회 · 정신건강의학",
        "tagline": "DSM-5 스크리닝 · 정신병리 위험 신호 (비진단)",
        "primary_lens": "정신병리( Psychopathology ) · DSM 스펙트럼 · 위험도",
        "what_we_optimize": [
            "DSM-5-TR 12영역 웰니스 스크리닝 (우울·불안·외상·수면·강박 등)",
            "PHQ-9·GAD-7·PCL-5·ISI·PSS 임상 스크린",
            "전문 기관 상담 고려 지표·clinical insight (참고용)",
            "정신과 연계 교육·CME 보조 (진료 대체 아님)",
        ],
        "what_we_de_emphasize": [
            "질병 진단명 단정·ICD/DSM 코드 부여",
            "약물 처방·용량·중단 권고",
            "타로·무의식 깊은 해석",
        ],
        "hero_stat": "DSM 스펙트럼 · 위험 스크리닝",
        "color": "#7c3aed",
        "icon": "🩺",
        "allowed_instruments": [
            "phq9",
            "gad7",
            "isi",
            "pss",
            "pcl5",
            "micro_emotion",
            "rses",
        ],
        "feature_flags": {
            "counseling_theories_full": False,
            "counseling_phases": True,
            "homework_packages": False,
            "tarot_bridge": False,
            "assessment_packages": True,
            "dsm5_catalog": True,
            "clinical_insight_risk": True,
            "psych_timeline": True,
            "b2b_export": True,
            "white_label": True,
        },
        "legal_framing_ko": (
            "정신의학회 라이선스는 **비진단 스크리닝·교육·CME 보조**입니다. "
            "의료행위·정신과 진료·처방을 제공하지 않으며, "
            "환자 진료·응급 대신 **전문의·의료기관 연계**를 전제로 합니다."
        ),
    },
    AssociationDiscipline.INTEGRATIVE.value: {
        "discipline_id": AssociationDiscipline.INTEGRATIVE.value,
        "label_ko": "통합학회 · 다학제",
        "tagline": "상담+심리+정신의학 협업 · 옴니디isciplinary",
        "primary_lens": "사례 + 측정 + DSM 스크리닝 통합",
        "what_we_optimize": [
            "3영역 기능 전체 · 학회 간 공동 교육",
            "타로·상담·검사·DSM 파이프라인 일원화",
            "B2B export · 화이트라벨",
        ],
        "what_we_de_emphasize": [],
        "hero_stat": "다학제 · 통합 리포트",
        "color": "#c4a574",
        "icon": "🔗",
        "allowed_instruments": "all",
        "feature_flags": {
            "counseling_theories_full": True,
            "counseling_phases": True,
            "homework_packages": True,
            "tarot_bridge": True,
            "assessment_packages": True,
            "dsm5_catalog": True,
            "clinical_insight_risk": True,
            "psych_timeline": True,
            "b2b_export": True,
            "white_label": True,
        },
        "legal_framing_ko": (
            "통합 라이선스는 **교육·연구·웰니스 협업**용입니다. "
            "각 학문 영역의 면허·윤리 규정을 준수하며, 진단·처방·응급 의료는 제공하지 않습니다."
        ),
    },
}

# ── 구독 등급 ─────────────────────────────────────────────────────────
LICENSE_TIERS: Dict[str, Dict[str, Any]] = {
    LicenseTier.CHAPTER.value: {
        "tier_id": LicenseTier.CHAPTER.value,
        "label_ko": "Chapter · 지부",
        "subtitle": "지회·동호회·소규모 연수",
        "seats": 30,
        "price_krw_yearly": 990_000,
        "price_label": "연 99만원",
        "includes": [
            "학회 유형 1종 선택",
            "월 500 세션",
            "기본 사용 리포트",
            "이메일 지원",
        ],
    },
    LicenseTier.SOCIETY.value: {
        "tier_id": LicenseTier.SOCIETY.value,
        "label_ko": "Society · 학회",
        "subtitle": "본회·정회원·연수원",
        "seats": 150,
        "price_krw_yearly": 2_900_000,
        "price_label": "연 290만원",
        "includes": [
            "학회 유형 1종 + 보조 영역 미리보기",
            "무제한 세션 (공정 사용)",
            "B2B 집계 export (해당 tier)",
            "학회 로고·명칭 co-brand",
            "전담 온보딩 1회",
        ],
        "recommended": True,
    },
    LicenseTier.FEDERATION.value: {
        "tier_id": LicenseTier.FEDERATION.value,
        "label_ko": "Federation · 연합",
        "subtitle": "대학·병원·연합학회·교육기관",
        "seats": 500,
        "price_krw_yearly": 7_900_000,
        "price_label": "연 790만원",
        "includes": [
            "학회 유형 2종 동시",
            "API · SSO 연동 상담",
            "감사 로그 · vault export",
            "슈퍼바이저·관리자 RBAC",
            "분기 리뷰 미팅",
        ],
    },
    LicenseTier.INSTITUTE.value: {
        "tier_id": LicenseTier.INSTITUTE.value,
        "label_ko": "Institute · 파트너",
        "subtitle": "연구소·플랫폼·공공·대기업 EAP",
        "seats": 9999,
        "price_krw_yearly": 0,
        "price_label": "별도 견적",
        "includes": [
            "전 영역 · 화이트라벨",
            "전용 인스턴스·SLA",
            "커스텀 검사·학파 패키지",
            "IRB·연구 데이터 파이프",
        ],
    },
}

TIER_FEATURE_OVERRIDES: Dict[str, Dict[str, bool]] = {
    LicenseTier.CHAPTER.value: {"b2b_export": False, "white_label": False},
    LicenseTier.SOCIETY.value: {"b2b_export": True, "white_label": False},
    LicenseTier.FEDERATION.value: {"b2b_export": True, "white_label": True},
    LicenseTier.INSTITUTE.value: {"b2b_export": True, "white_label": True},
}


def list_disciplines() -> List[Dict[str, Any]]:
    return list(DISCIPLINE_PROFILES.values())


def list_license_tiers() -> List[Dict[str, Any]]:
    return list(LICENSE_TIERS.values())


def build_associations_catalog() -> Dict[str, Any]:
    comparison_rows = [
        {
            "dimension": "핵심 관점",
            "counseling": "사례·관계·상담 과정",
            "psychology": "측정·데이터·종단 추적",
            "psychiatry": "DSM 스펙트럼·위험 스크리닝",
        },
        {
            "dimension": "주요 도구",
            "counseling": "상담 이론 19종 · SCT · 애착 · 타로 거울",
            "psychology": "검사 배터리 · 기분 5축 · psych 프로파일",
            "psychiatry": "PHQ-9·GAD-7·PCL-5 · DSM 영역 · insight",
        },
        {
            "dimension": "적합 학회",
            "counseling": "한국상담학회, 가족치료학회, 학교상담 등",
            "psychology": "한국심리학회, 임상·상담심리 전문학회 등",
            "psychiatry": "대한정신의학회, 지역 정신의학회 등",
        },
        {
            "dimension": "진단·처방",
            "counseling": "❌ (웰니스·교육)",
            "psychology": "❌ (비진단 스크리닝)",
            "psychiatry": "❌ (스크리닝만 · 의료 연계)",
        },
    ]
    return {
        "product_name": "마음쉼터 Association License",
        "tagline": "상담 · 심리 · 정신의학 학회를 위한 AI 웰니스·교육 플랫폼",
        "disclaimer": (
            "모든 라이선스는 AI 웰니스·교육·연구 보조 도구입니다. "
            "면허 진료·임상치료·공식 심리검사 실시·진단·처방을 대체하지 않습니다."
        ),
        "disciplines": list_disciplines(),
        "license_tiers": list_license_tiers(),
        "comparison_matrix": comparison_rows,
        "collaboration_models": [
            {
                "model": "학회 공식 제휴",
                "description": "정회원·수련생 대상 co-brand 앱 · 연수·워크숍 실습 도구",
            },
            {
                "model": "CME·연수원",
                "description": "사례 개념화·DSM 스크리닝·측정 해석 교육용 샌드박스",
            },
            {
                "model": "연구·IRB",
                "description": "익명 집계 export · 종단 psych timeline (동의 하)",
            },
        ],
    }


def resolve_entitlements(
    discipline_id: str,
    tier_id: str,
    *,
    secondary_discipline: Optional[str] = None,
) -> Dict[str, Any]:
    profile = DISCIPLINE_PROFILES.get(discipline_id) or DISCIPLINE_PROFILES[AssociationDiscipline.COUNSELING.value]
    tier = LICENSE_TIERS.get(tier_id) or LICENSE_TIERS[LicenseTier.SOCIETY.value]
    flags = dict(profile.get("feature_flags") or {})
    flags.update(TIER_FEATURE_OVERRIDES.get(tier_id, {}))

    instruments: Set[str]
    allowed = profile.get("allowed_instruments")
    if allowed == "all":
        from app.assessments.registry import all_instrument_ids

        instruments = set(all_instrument_ids())
    else:
        instruments = set(allowed or [])

    if secondary_discipline and tier_id in (LicenseTier.FEDERATION.value, LicenseTier.INSTITUTE.value):
        sec = DISCIPLINE_PROFILES.get(secondary_discipline, {})
        sec_allowed = sec.get("allowed_instruments")
        if sec_allowed == "all":
            from app.assessments.registry import all_instrument_ids

            instruments |= set(all_instrument_ids())
        elif isinstance(sec_allowed, list):
            instruments |= set(sec_allowed)

    plan_override = "PREMIUM" if tier_id in (LicenseTier.SOCIETY.value, LicenseTier.FEDERATION.value, LicenseTier.INSTITUTE.value) else "PLUS"

    return {
        "discipline_id": discipline_id,
        "discipline_label": profile.get("label_ko"),
        "primary_lens": profile.get("primary_lens"),
        "tier_id": tier_id,
        "tier_label": tier.get("label_ko"),
        "seats": tier.get("seats"),
        "plan_override": plan_override,
        "allowed_instruments": sorted(instruments),
        "feature_flags": flags,
        "legal_framing_ko": profile.get("legal_framing_ko"),
        "tarot_enabled": flags.get("tarot_bridge", True),
        "dsm_enabled": flags.get("dsm5_catalog", False),
    }


def instrument_allowed(instrument_id: str, entitlements: Optional[Dict[str, Any]]) -> bool:
    if not entitlements:
        return True
    allowed = entitlements.get("allowed_instruments") or []
    return instrument_id in allowed


def feature_enabled(flag: str, entitlements: Optional[Dict[str, Any]]) -> bool:
    if not entitlements:
        return True
    return bool((entitlements.get("feature_flags") or {}).get(flag, True))
