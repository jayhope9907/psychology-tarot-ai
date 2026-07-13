"""소비자 첫 화면용 가이드 경로 — 전체 카탈로그를 바로 보여 주지 않는다."""
from __future__ import annotations

from typing import Any, Dict, List

# 오늘·지금 바로 쓸 짧은 길 (교육용·비진단)
STARTER_INSTRUMENT_IDS: List[str] = [
    "micro_emotion",
    "who5",
    "rses",
    "self_efficacy_gse",
    "phq9",
    "gad7",
    "isi",
    "verbal_fluency_screen",
    "communication_assertiveness",
]

# 카탈로그에서 “더보기” 전에 강조할 주제 순서
FEATURED_DOMAIN_LABELS: List[str] = [
    "자존감·웰빙",
    "언어심리",
    "긍정 웰빙",
    "임상 정서",
    "불안",
]

CONSUMER_COPY = {
    "primary_cta": "지금 마음, 2분만 이야기해요",
    "primary_cta_sub": "검사·진단이 아니라, 이서연과 편하게 나누는 시간이에요.",
    "catalog_hint": "전체를 다 할 필요 없어요. 오늘은 하나만 골라도 충분해요.",
    "battery_friendly": "오늘은 짧은 확인만 해도 괜찮아요.",
}


def guided_catalog_slice(formal_instruments: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_id = {i.get("instrument_id"): i for i in formal_instruments}
    starters = []
    for iid in STARTER_INSTRUMENT_IDS:
        item = by_id.get(iid)
        if item:
            starters.append(
                {
                    "instrument_id": iid,
                    "user_title": item.get("user_title") or item.get("display_name"),
                    "intro": item.get("intro") or item.get("focus") or "",
                    "domain_label": item.get("domain_label"),
                    "item_count": item.get("item_count"),
                    "why": "오늘 가볍게 시작하기 좋아요",
                }
            )
    return {
        "headline": "오늘 추천 · 짧은 길",
        "subheadline": CONSUMER_COPY["catalog_hint"],
        "starters": starters,
        "copy": CONSUMER_COPY,
    }
