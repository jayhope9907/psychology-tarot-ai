"""Process-Based Therapy (PBT) + Feedback-Informed Treatment (FIT) architecture layer.

근거 문헌(비주장):
- Hayes & Hofmann (2017/2019) process-based therapy
- Wampold / Norcross common factors & alliance
- Lambert routine outcome monitoring / client feedback

Therapy biomarker 벡터 → 과정 차원(openness / awareness / engagement)과
세션 피드백(alliance·progress) 힌트로 변환한다. 비진단.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

from app.services.therapy_evidence_corpus import list_evidence_papers


def _n(mapping: Mapping[str, Any], key: str, default: float = 50.0) -> float:
    try:
        value = mapping.get(key, default)
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _clamp(n: float) -> float:
    if n != n:
        return 0.0
    return max(0.0, min(100.0, n))


def _avg(values: List[float]) -> float:
    if not values:
        return 50.0
    return sum(values) / len(values)


def extract_process_dimensions(vector: Mapping[str, Any]) -> Dict[str, Any]:
    """Map school scores → PBT-style process dimensions (0–100)."""
    openness = _avg(
        [
            _n(vector, "actValuesScore"),
            _n(vector, "acceptanceScore"),
            _n(vector, "cftCompassionScore"),
            _n(vector, "mbctDecenteringScore"),
        ]
    )
    awareness = _avg(
        [
            _n(vector, "mindfulnessScore"),
            _n(vector, "gestaltPresenceScore"),
            _n(vector, "mbctDecenteringScore"),
            _n(vector, "insightScore"),
        ]
    )
    engagement = _avg(
        [
            _n(vector, "solutionScore"),
            _n(vector, "baActivationScore"),
            _n(vector, "realityScore"),
            _n(vector, "miChangeTalkScore"),
            _n(vector, "courageScore"),
        ]
    )
    regulation = _avg(
        [
            _n(vector, "dbtRegulationScore"),
            _n(vector, "traumaSafetyScore"),
            _n(vector, "polyvagalSafetyScore"),
            _n(vector, "seTitrationScore"),
        ]
    )
    relatedness = _avg(
        [
            _n(vector, "eftBondScore"),
            _n(vector, "attachmentSecureScore"),
            _n(vector, "iptRoleScore"),
            _n(vector, "ifsSelfLeadershipScore"),
        ]
    )

    flexibility = _clamp((openness + awareness + engagement) / 3.0)
    bottlenecks = sorted(
        [
            ("openness", round(openness, 1)),
            ("awareness", round(awareness, 1)),
            ("engagement", round(engagement, 1)),
            ("regulation", round(regulation, 1)),
            ("relatedness", round(relatedness, 1)),
        ],
        key=lambda x: x[1],
    )
    lowest = bottlenecks[0][0]

    focus_map = {
        "openness": {
            "process": "openness",
            "suggested_schools": ["ACT", "CFT", "ROGERIAN"],
            "coach_ko": "판단 없이 경험을 열어두는 연습(수용·자기자비)을 우선하세요.",
        },
        "awareness": {
            "process": "awareness",
            "suggested_schools": ["MINDFULNESS", "MBCT", "GESTALT"],
            "coach_ko": "지금-여기 감각·생각 알아차림을 짧게 반복하세요.",
        },
        "engagement": {
            "process": "engagement",
            "suggested_schools": ["BEHAVIORAL_ACTIVATION", "SOLUTION_FOCUSED", "MOTIVATIONAL"],
            "coach_ko": "가치에 맞는 아주 작은 행동 하나를 오늘 안에 실행하세요.",
        },
        "regulation": {
            "process": "regulation",
            "suggested_schools": ["DBT", "POLYVAGAL_INFORMED", "TRAUMA_INFORMED"],
            "coach_ko": "안전·안정화·고통감내 스킬을 먼저 확보하세요.",
        },
        "relatedness": {
            "process": "relatedness",
            "suggested_schools": ["EFT", "ATTACHMENT", "IFS"],
            "coach_ko": "관계·내면 파트와의 안전한 연결을 천천히 살펴보세요.",
        },
    }

    return {
        "openness": round(openness, 1),
        "awareness": round(awareness, 1),
        "engagement": round(engagement, 1),
        "regulation": round(regulation, 1),
        "relatedness": round(relatedness, 1),
        "psychologicalFlexibilityProxy": round(flexibility, 1),
        "primaryBottleneck": lowest,
        "focus": focus_map[lowest],
        "non_diagnostic": True,
        "evidence_paper_ids": [
            "hayes_hofmann_2017_pbt",
            "hofmann_hayes_2019_pbt",
            "barlow_2017_unified",
        ],
    }


def build_fit_feedback(
    *,
    progress_score: Optional[float] = None,
    alliance_score: Optional[float] = None,
    process_dims: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """FIT/ROM-inspired session feedback (0–100). Missing → neutral 50."""
    progress = _clamp(50.0 if progress_score is None else float(progress_score))
    alliance = _clamp(50.0 if alliance_score is None else float(alliance_score))
    dims = process_dims or {}
    flexibility = _n(dims, "psychologicalFlexibilityProxy", 50.0)

    risk_flags: List[str] = []
    if progress < 35:
        risk_flags.append("low_progress")
    if alliance < 40:
        risk_flags.append("alliance_strain")
    if flexibility < 35:
        risk_flags.append("low_flexibility")

    if risk_flags:
        recommendation_ko = (
            "피드백상 조율이 필요해 보여요. 속도를 낮추고 관계·안전·작은 성공 경험을 우선하세요."
        )
        stance = "repair"
    elif progress >= 70 and alliance >= 65:
        recommendation_ko = "흐름이 좋아요. 지금 도움 되는 과정을 한 가지 더 구체화해 이어가세요."
        stance = "amplify"
    else:
        recommendation_ko = "안정적이에요. 병목 과정 하나를 고르고 짧은 실험으로 확인해 보세요."
        stance = "explore"

    return {
        "progressScore": round(progress, 1),
        "allianceScore": round(alliance, 1),
        "flexibilityProxy": round(flexibility, 1),
        "riskFlags": risk_flags,
        "stance": stance,
        "recommendation_ko": recommendation_ko,
        "non_diagnostic": True,
        "evidence_paper_ids": [
            "lambert_2010_rom",
            "norcross_2019_relations",
            "wampold_2015_common",
        ],
    }


def trauma_safety_gate(vector: Mapping[str, Any]) -> Dict[str, Any]:
    """Polyvagal/trauma-informed intensity gate (wellness — not neurological diagnosis)."""
    safety = _avg(
        [
            _n(vector, "traumaSafetyScore"),
            _n(vector, "polyvagalSafetyScore"),
            _n(vector, "emdrStabilizeScore"),
            _n(vector, "seTitrationScore"),
            _n(vector, "dbtRegulationScore"),
        ]
    )
    if safety < 40:
        level = "stabilize"
        allow_intense = False
        note = "안전·안정화 모드: 강한 노출·재처리 안내는 보류하고 자원·호흡·경계를 우선합니다."
    elif safety < 65:
        level = "titrate"
        allow_intense = False
        note = "타이틀레이션 모드: 짧은 자각과 선택권 확인 후 약한 탐색만 허용합니다."
    else:
        level = "engage"
        allow_intense = True
        note = "안전 신호가 비교적 충분해 보여 과정 실험을 조심스럽게 진행할 수 있습니다."

    return {
        "safetyScore": round(safety, 1),
        "level": level,
        "allowIntenseExploration": allow_intense,
        "note_ko": note,
        "non_diagnostic": True,
        "evidence_paper_ids": [
            "porges_2022_polyvagal",
            "levine_2010_se",
            "resick_2017_cpt",
            "foa_2007_pe",
        ],
    }


def aai_attachment_coherence(vector: Mapping[str, Any]) -> Dict[str, Any]:
    """AAI-informed coherence proxy (not Adult Attachment Interview scoring)."""
    secure = _n(vector, "attachmentSecureScore", 50.0)
    eft = _n(vector, "eftBondScore", 50.0)
    ifs_self = _n(vector, "ifsSelfLeadershipScore", 50.0)
    narrative = _n(vector, "narrativeAgencyScore", 50.0)
    coherence = _clamp(_avg([secure, eft, ifs_self, narrative]))

    if coherence >= 70:
        state = "coherent_secure_lean"
        coach = "관계 서술이 비교적 일관돼 보여요. 안전기지·연결 경험을 구체 장면으로 이어가세요."
    elif coherence >= 45:
        state = "mixed_or_organizing"
        coach = "관계 이야기에 엇갈림이 있을 수 있어요. 한 장면만 골라 감정·욕구를 천천히 정리해 보세요."
    else:
        state = "incoherent_or_dismissing_lean"
        coach = "관계 서술이 막히거나 끊길 수 있어요. 평가 없이 ‘지금 느껴지는 안전감’부터 짧게 말해 보세요."

    return {
        "coherenceProxy": round(coherence, 1),
        "stateHint": state,
        "coach_ko": coach,
        "non_diagnostic": True,
        "not_aai_scoring": True,
        "evidence_paper_ids": [
            "van_ijzendoorn_1995_aai",
            "bakermans_1993_aai_psychometric",
            "main_1985_aai_protocol",
        ],
    }


def pesm_ecological_systems(vector: Mapping[str, Any]) -> Dict[str, Any]:
    """PESM-inspired multi-level wellness context (micro→macro), non-diagnostic."""
    micro = _avg(
        [
            _n(vector, "mindfulnessScore"),
            _n(vector, "acceptanceScore"),
            _n(vector, "dbtRegulationScore"),
            _n(vector, "actValuesScore"),
        ]
    )
    meso = _avg(
        [
            _n(vector, "eftBondScore"),
            _n(vector, "attachmentSecureScore"),
            _n(vector, "iptRoleScore"),
            _n(vector, "ifsSelfLeadershipScore"),
        ]
    )
    exo = _avg(
        [
            _n(vector, "solutionScore"),
            _n(vector, "baActivationScore"),
            _n(vector, "realityScore"),
            _n(vector, "miChangeTalkScore"),
        ]
    )
    macro = _avg(
        [
            _n(vector, "multiculturalHumilityScore", 50.0),
            _n(vector, "feministEmpowermentScore", 50.0),
            _n(vector, "bowenDifferentiationScore", 50.0),
            _n(vector, "strengthsScore"),
        ]
    )
    layers = {
        "micro_individual": round(micro, 1),
        "meso_relational": round(meso, 1),
        "exo_activity_context": round(exo, 1),
        "macro_cultural_structural": round(macro, 1),
    }
    weakest = min(layers.items(), key=lambda x: x[1])[0]
    focus_ko = {
        "micro_individual": "개인 조절·알아차림(미시) 층을 우선하세요.",
        "meso_relational": "관계·애착·역할(중간체계) 층을 우선하세요.",
        "exo_activity_context": "일상 활동·환경 맥락(외체계) 층을 우선하세요.",
        "macro_cultural_structural": "문화·권력·구조 맥락(거시) 층을 우선하세요.",
    }[weakest]

    return {
        "layers": layers,
        "primaryLayerFocus": weakest,
        "focus_ko": focus_ko,
        "balanceScore": round(_avg(list(layers.values())), 1),
        "non_diagnostic": True,
        "evidence_paper_ids": ["reeb_2018_pesm"],
    }


def build_paper_architecture_bundle(
    vector: Mapping[str, Any],
    *,
    progress_score: Optional[float] = None,
    alliance_score: Optional[float] = None,
) -> Dict[str, Any]:
    process_dims = extract_process_dimensions(vector)
    fit = build_fit_feedback(
        progress_score=progress_score,
        alliance_score=alliance_score,
        process_dims=process_dims,
    )
    safety = trauma_safety_gate(vector)
    aai = aai_attachment_coherence(vector)
    pesm = pesm_ecological_systems(vector)
    return {
        "process_based_therapy": process_dims,
        "fit_session_feedback": fit,
        "trauma_safety_gate": safety,
        "aai_attachment_coherence": aai,
        "pesm_ecological_systems": pesm,
        "evidence_papers": list_evidence_papers(hook="process_based_therapy")
        + list_evidence_papers(hook="fit_session_feedback")
        + list_evidence_papers(hook="trauma_safety_gate")
        + list_evidence_papers(hook="aai_attachment_coherence")
        + list_evidence_papers(hook="pesm_ecological_systems"),
        "architecture_modules": [
            {
                "id": "process_based_therapy",
                "path": "app/services/process_based_therapy.py",
                "role": "PBT process dimensions from biomarker vector",
            },
            {
                "id": "fit_session_feedback",
                "path": "app/services/process_based_therapy.py",
                "role": "ROM/FIT-inspired progress & alliance feedback",
            },
            {
                "id": "trauma_safety_gate",
                "path": "app/services/process_based_therapy.py",
                "role": "Safety/titration gate before intense exploration prompts",
            },
            {
                "id": "aai_attachment_coherence",
                "path": "app/services/process_based_therapy.py",
                "role": "AAI-informed narrative coherence proxy (not AAI scoring)",
            },
            {
                "id": "pesm_ecological_systems",
                "path": "app/services/process_based_therapy.py",
                "role": "PESM multi-level ecological context layer",
            },
            {
                "id": "therapy_evidence_corpus",
                "path": "app/services/therapy_evidence_corpus.py",
                "role": "DOI-linked papers mapped to schools & hooks",
            },
        ],
        "non_diagnostic": True,
    }
