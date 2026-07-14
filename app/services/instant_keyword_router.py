"""즉시 키워드 반응 라우터 — 특허 후보 INV-09.

메시지에 등장한 키워드를 학파·기법·앱 기능에 즉시 가중 매핑합니다.
일반 공감 키워드보다 도메인 특화 키워드(중독·트라우마·가족 등)를 우선합니다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from app.models.clinical import ClinicalSchool
from app.services.counseling_theories import THEORY_CATALOG, get_theory_meta

# 흔해서 단독으로 특정 학파를 차지하면 안 되는 키워드 (저가중)
GENERIC_KEYWORDS = frozenset(
    {
        "힘들",
        "힘드",
        "울",
        "아프",
        "생각",
        "왜",
        "괜찮",
        "모르겠",
        "해야",
        "계속",
        "또",
        "실패",
        "망했",
        "버텨",
        "지쳐",
        "슬프",
        "상처",
        "외로",
        "무너",
        "판단",
        "실수",
        "이유",
        "논리",
        "분석",
        "습관",
        "변화",
        "관계",
        "가족",
        "친구",
    }
)

CATEGORY_PRIORITY = {
    "substance_addiction": 2.4,
    "brief_emotion": 1.35,
    "cognitive_behavioral": 1.2,
    "systemic": 1.15,
    "psychodynamic": 1.05,
    "expressive": 1.1,
    "humanistic": 0.9,
    "integrative": 0.8,
}

# 앱 기능 즉시 반응 (웰니스 내비)
FEATURE_KEYWORD_MAP: Dict[str, Dict[str, Any]] = {
    "tarot": {
        "keywords": ("타로", "카드 뽑아", "카드뽑", "리딩", "아르카나"),
        "route": "/tarot",
        "label_ko": "3D 타로 성찰",
        "hint": "상징 거울로 가볍게 비춰보고 싶을 수 있어요. 강요하지 말고 선택지로만.",
    },
    "psychometrics": {
        "keywords": ("MBTI", "엠비티아이", "성격유형", "빅파이브", "심리검사", "척도"),
        "route": "/psychometrics",
        "label_ko": "MBTI·심리 탐색",
        "hint": "검사가 필요하면 비진단 스크리닝·성격 탐색을 부드럽게 안내.",
    },
    "picture": {
        "keywords": ("그림", "그림검사", "집나무사람", "HTP", "만다라", "낙서"),
        "route": "/picture-assessment",
        "label_ko": "그림·이야기 표현",
        "hint": "말로 어렵다면 그림·이야기 표현 도구를 살며시 제안.",
    },
    "expressive": {
        "keywords": ("역할극", "사이코드라마", "표현치료", "빈 의자", "연극치료"),
        "route": "/expressive",
        "label_ko": "표현·역할 상담",
        "hint": "표현·역할 기법이 맞을 수 있음. 선택권 존중.",
    },
    "addiction_support": {
        "keywords": ("중독", "술", "담배", "마약", "단주", "단약", "갈망", "재발", "금단", "해독"),
        "route": "/api/v1/addiction/corpus",
        "label_ko": "중독·습관 회복 지원",
        "hint": "중독 웰니스 기법( MI·CBT·RP 등)을 쓰되 의료 대체 금지. 1332 연계 우선.",
    },
    "crisis": {
        "keywords": ("죽고", "자살", "끝내고", "자해", "사라지고 싶"),
        "route": "/legal",
        "label_ko": "위기 연계",
        "hint": "즉시 위기 프로토콜·1393·119. 일반 탐색 중단.",
    },
    "mood_checkin": {
        "keywords": ("오늘 기분", "체크인", "입체 기분", "기분점수"),
        "route": "/home",
        "label_ko": "오늘 마음 체크인",
        "hint": "5축 기분 맥락을 가볍게 반영.",
    },
}


@dataclass
class InstantReaction:
    school: ClinicalSchool
    score: float
    reason: str
    matched_keywords: List[str] = field(default_factory=list)
    school_scores: List[Dict[str, Any]] = field(default_factory=list)
    techniques: List[str] = field(default_factory=list)
    features: List[Dict[str, Any]] = field(default_factory=list)
    technique_hits: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "school": self.school.value,
            "score": round(self.score, 3),
            "reason": self.reason,
            "matched_keywords": self.matched_keywords[:12],
            "school_scores": self.school_scores[:5],
            "techniques": self.techniques[:6],
            "features": self.features[:4],
            "technique_hits": self.technique_hits[:4],
        }


def _keyword_weight(keyword: str, category: str) -> float:
    base = 1.0 + min(2.5, len(keyword) / 4.0)
    if keyword in GENERIC_KEYWORDS:
        base *= 0.35
    base *= CATEGORY_PRIORITY.get(category, 1.0)
    return base


@lru_cache(maxsize=1)
def _theory_keyword_index() -> Tuple[Tuple[str, str, float, Tuple[str, ...]], ...]:
    """(keyword, school_value, weight, techniques) immutable cache."""
    rows: List[Tuple[str, str, float, Tuple[str, ...]]] = []
    for school, meta in THEORY_CATALOG.items():
        if school == ClinicalSchool.INTEGRATIVE:
            continue
        category = meta.get("category") or "integrative"
        techniques = tuple(meta.get("techniques") or ())
        for kw in meta.get("routing_keywords") or ():
            kw_n = (kw or "").strip().lower()
            if not kw_n:
                continue
            rows.append((kw_n, school.value, _keyword_weight(kw_n, category), techniques))
    # Longer keywords first for greedy highlight
    rows.sort(key=lambda r: -len(r[0]))
    return tuple(rows)


def _score_schools(corpus: str) -> Dict[str, Dict[str, Any]]:
    scores: Dict[str, Dict[str, Any]] = {}
    for keyword, school_v, weight, techniques in _theory_keyword_index():
        if keyword not in corpus:
            continue
        bucket = scores.setdefault(
            school_v,
            {"score": 0.0, "keywords": [], "techniques": list(techniques)},
        )
        bucket["score"] += weight
        if keyword not in bucket["keywords"]:
            bucket["keywords"].append(keyword)
    return scores


def _match_features(corpus: str) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for feature_id, meta in FEATURE_KEYWORD_MAP.items():
        matched = [kw for kw in meta["keywords"] if kw.lower() in corpus]
        if not matched:
            continue
        hits.append(
            {
                "feature_id": feature_id,
                "label_ko": meta["label_ko"],
                "route": meta["route"],
                "matched_keywords": matched,
                "hint": meta["hint"],
                "priority": len("".join(matched)),
            }
        )
    hits.sort(key=lambda x: -x["priority"])
    return hits


def _match_addiction_techniques(corpus: str) -> List[Dict[str, Any]]:
    try:
        from app.services.addiction_theories import ADDICTION_TECHNIQUE_ONTOLOGY
    except Exception:
        return []
    hits: List[Dict[str, Any]] = []
    for tech in ADDICTION_TECHNIQUE_ONTOLOGY:
        name = (tech.get("name_ko") or "").lower()
        steps = " ".join(tech.get("steps") or []).lower()
        blob = f"{name} {steps} {' '.join(tech.get('schools') or [])}".lower()
        # Soft heuristic: if any school keyword already in corpus and phase-relevant tokens
        tokens = [t for t in (name.replace("·", " ").split() + list(tech.get("steps") or [])[:2]) if len(t) >= 2]
        matched = [t for t in tokens if t.lower() in corpus]
        if not matched and not any(
            kw in corpus for kw in ("갈망", "재발", "술", "중독", "담배", "거절", "단주", "단약")
        ):
            continue
        if matched or any(kw in corpus for kw in ("갈망", "재발", "술", "중독")):
            if tech["id"] == "urge_surfing" and "갈망" not in corpus and "충동" not in corpus:
                continue
            if matched or tech["id"] in {"functional_analysis", "high_risk_map", "decisional_balance", "oars"}:
                hits.append(
                    {
                        "id": tech["id"],
                        "name_ko": tech["name_ko"],
                        "phase": tech.get("phase"),
                        "schools": tech.get("schools") or [],
                        "matched": matched[:4],
                    }
                )
    return hits[:5]


def react_instantly(
    user_message: str,
    recent_messages: Optional[List[Dict[str, str]]] = None,
    preferred_school: Optional[ClinicalSchool] = None,
) -> InstantReaction:
    recent = " ".join(
        (entry.get("content") or "") for entry in (recent_messages or [])[-3:] if entry.get("role") == "user"
    )
    corpus = f"{user_message} {recent}".lower()

    if preferred_school:
        meta = get_theory_meta(preferred_school)
        return InstantReaction(
            school=preferred_school,
            score=99.0,
            reason="user_selected",
            matched_keywords=[],
            techniques=list(meta.get("techniques") or [])[:6],
            features=_match_features(corpus),
            technique_hits=_match_addiction_techniques(corpus),
        )

    scored = _score_schools(corpus)
    features = _match_features(corpus)
    tech_hits = _match_addiction_techniques(corpus)

    # Feature crisis force
    if any(f["feature_id"] == "crisis" for f in features):
        school = ClinicalSchool.TRAUMA_INFORMED
        return InstantReaction(
            school=school,
            score=100.0,
            reason="crisis_keyword_instant",
            matched_keywords=["위기"],
            techniques=list(get_theory_meta(school).get("techniques") or [])[:6],
            features=features,
            technique_hits=tech_hits,
        )

    if not scored:
        school = ClinicalSchool.INTEGRATIVE
        return InstantReaction(
            school=school,
            score=0.0,
            reason="no_keyword_hit",
            techniques=list(get_theory_meta(school).get("techniques") or [])[:6],
            features=features,
            technique_hits=tech_hits,
        )

    ranked = sorted(scored.items(), key=lambda item: -item[1]["score"])
    top_school_v, top = ranked[0]
    school = ClinicalSchool(top_school_v)
    school_scores = [
        {"school": s, "score": round(data["score"], 3), "keywords": data["keywords"][:6]}
        for s, data in ranked[:5]
    ]

    # Boost addiction CBT / RP when substance feature hits
    if any(f["feature_id"] == "addiction_support" for f in features):
        for cand in (
            ClinicalSchool.ADDICTION_CBT,
            ClinicalSchool.RELAPSE_PREVENTION,
            ClinicalSchool.MOTIVATIONAL,
            ClinicalSchool.CRAVING_MINDFULNESS,
        ):
            data = scored.get(cand.value)
            if data and data["score"] >= top["score"] * 0.55:
                school = cand
                top = data
                break
        else:
            if school.value not in scored or CATEGORY_PRIORITY.get(get_theory_meta(school)["category"], 1) < 2:
                school = ClinicalSchool.ADDICTION_CBT
                top = scored.get(school.value) or {"score": top["score"] + 1, "keywords": ["중독"], "techniques": []}

    meta = get_theory_meta(school)
    techniques = list(dict.fromkeys((top.get("techniques") or []) + list(meta.get("techniques") or [])))[:6]
    return InstantReaction(
        school=school,
        score=float(top.get("score") or 0),
        reason="instant_weighted_keyword",
        matched_keywords=list(top.get("keywords") or [])[:12],
        school_scores=school_scores,
        techniques=techniques,
        features=features,
        technique_hits=tech_hits,
    )


def build_instant_reaction_prompt(reaction: InstantReaction) -> str:
    meta = get_theory_meta(reaction.school)
    lines = [
        "## [즉시] 키워드 반응 라우팅 (이번 메시지 우선)",
        f"- 매칭 학파: **{meta['label']}** ({reaction.reason}, score={reaction.score:.2f})",
    ]
    if reaction.matched_keywords:
        lines.append(f"- 감지 키워드: {', '.join(reaction.matched_keywords[:8])}")
    if reaction.techniques:
        lines.append(f"- 즉시 적용 기법: {' · '.join(reaction.techniques[:5])}")
    if reaction.technique_hits:
        names = ", ".join(t["name_ko"] for t in reaction.technique_hits[:3])
        lines.append(f"- 중독/습관 기법 카드: {names}")
    for feat in reaction.features[:3]:
        lines.append(f"- 기능 신호[{feat['label_ko']}]: {feat['hint']}")
    lines.append(
        "- **이번 사용자 말의 구체 키워드에 바로 반응**하고, 직전 턴과 같은 공감 멘트·같은 질문을 반복하지 마세요."
    )
    lines.append("- 진단·처방·해독·의료 대체를 하지 마세요. 위기면 전문 연계를 우선하세요.")
    return "\n".join(lines)
