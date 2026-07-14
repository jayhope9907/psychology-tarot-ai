"""전 제품 기능 → 특허 후보 발명 맵 (출원 준비용, 비주장)."""
from __future__ import annotations

from typing import Any, Dict, List

from app.services.addiction_theories import ADDICTION_THEORIES, ADDICTION_TECHNIQUE_ONTOLOGY
from app.services.counseling_theories import THEORY_CATALOG
from app.services.product_surfaces import product_surfaces
from app.services.research_export import INVENTION_IDS

PLATFORM_INVENTIONS: List[Dict[str, Any]] = [
    *INVENTION_IDS,
    {
        "id": "INV-09",
        "title_ko": "가중 키워드 즉시반응 다층 라우팅 엔진",
        "title_en": "Weighted multi-layer instant keyword reaction router",
        "claim_sketch": (
            "메시지 키워드를 학파·기법·앱기능에 가중 매핑하고, "
            "일반어보다 도메인 특화어를 우선해 즉시 지시문을 주입하는 방법"
        ),
        "modules": ["instant_keyword_router", "persona_router", "chat_stream", "addiction_theories"],
        "covers": ["AI assistant", "all theory techniques", "feature deep-links"],
    },
    {
        "id": "INV-10",
        "title_ko": "입체 기분(5축) 맞춤 상담·검사 게이팅",
        "title_en": "Five-axis mood-conditioned counseling and assessment gating",
        "claim_sketch": "입체 체크인 좌표에 따라 톤·검사 제안 시점을 조건 분기하는 웰니스 방법",
        "modules": ["mood_assistant", "mood_dimensions", "daily_routine", "assessment_package"],
        "covers": ["mood check-in", "assessment soft nudge"],
    },
    {
        "id": "INV-11",
        "title_ko": "오프라인 키워드 번들 상담·타로 캐시 동기화",
        "title_en": "Offline keyword-counsel and tarot cache synchronization",
        "claim_sketch": "네트워크 단절 시 키워드 룰·덱 번들로 폴백하고 온라인 복귀 시 큐를 동기화",
        "modules": ["counsel_offline", "chat-offline.js", "tarot deck bundle", "sw.js"],
        "covers": ["offline chat", "PWA", "tarot offline"],
    },
    {
        "id": "INV-12",
        "title_ko": "소비자 개방·기관 라이선스 이중 제품 분리",
        "title_en": "Consumer-open vs association-license dual-surface product architecture",
        "claim_sketch": "동일 코어에서 소비자 개방 라우트와 라이선스 게이트 라우트를 권한으로 분리 제공하는 시스템",
        "modules": ["product_surfaces", "consumer_access", "association_licensing"],
        "covers": ["B2C", "B2B associations", "disability line"],
    },
]


def build_platform_ip_map() -> Dict[str, Any]:
    surfaces = product_surfaces()
    return {
        "document_id": "platform-ip-map-v2",
        "non_claims": [
            "본 문서는 특허 등록 사실을 주장하지 않습니다.",
            "의료 진단·치료 효능·의료기기 성능을 주장하지 않습니다.",
            "실제 청구항은 변리사 prior art 조사 후 확정합니다.",
        ],
        "theory_count": len(THEORY_CATALOG),
        "addiction_theory_count": len(ADDICTION_THEORIES),
        "addiction_technique_count": len(ADDICTION_TECHNIQUE_ONTOLOGY),
        "invention_count": len(PLATFORM_INVENTIONS),
        "inventions": PLATFORM_INVENTIONS,
        "product_surfaces": surfaces,
        "feature_claim_matrix": [
            {"feature": "AI chat orchestrator", "inv": ["INV-01", "INV-08", "INV-09"]},
            {"feature": "Association license routing", "inv": ["INV-02", "INV-12"]},
            {"feature": "License case seed", "inv": ["INV-03"]},
            {"feature": "Tarot / symbolic bridge", "inv": ["INV-04", "INV-11"]},
            {"feature": "Projective / picture assessment", "inv": ["INV-05"]},
            {"feature": "User ALG fingerprint", "inv": ["INV-06"]},
            {"feature": "Addiction theories & techniques", "inv": ["INV-07", "INV-09"]},
            {"feature": "Mood 5-axis gating", "inv": ["INV-10"]},
            {"feature": "Offline counsel/tarot", "inv": ["INV-11"]},
            {"feature": "Consumer vs B2B surfaces", "inv": ["INV-12"]},
        ],
    }
