"""앱 표면(유저 · 라이선스 · 장애인용) — 진입점 단일 정의."""
from __future__ import annotations

from typing import Any, Dict, List

from app.services.consumer_access import B2B_SEPARATE_NOTE_KO, consumer_open
from app.services.disability_product import disability_product_manifest


def product_surfaces() -> Dict[str, Any]:
    """배포·헬스·문서용 제품선 매니페스트."""
    consumer_routes: List[Dict[str, str]] = [
        {"id": "app", "label_ko": "통합 앱", "route": "/"},
        {"id": "home", "label_ko": "오늘 마음", "route": "/home"},
        {"id": "chat", "label_ko": "AI 대화", "route": "/chat"},
        {"id": "tarot", "label_ko": "타로", "route": "/tarot"},
        {"id": "clinical", "label_ko": "마음 돌보기", "route": "/clinical"},
        {"id": "psychometrics", "label_ko": "MBTI·탐색", "route": "/psychometrics"},
        {"id": "picture_assessment", "label_ko": "그림·이야기 표현", "route": "/picture-assessment"},
    ]
    license_routes: List[Dict[str, str]] = [
        {"id": "associations", "label_ko": "학회 라이선스", "route": "/associations"},
        {"id": "theories", "label_ko": "이론·학자·미술치료", "route": "/theories", "gate": "license_key"},
        {"id": "expressive", "label_ko": "표현·역할·미술", "route": "/expressive", "gate": "license_key"},
        {"id": "case_notes", "label_ko": "케이스 노트 AI", "route": "/case-notes", "status": "coming_soon"},
    ]
    disability = disability_product_manifest()
    return {
        "consumer_open": consumer_open(),
        "b2b_note_ko": B2B_SEPARATE_NOTE_KO,
        "lines": [
            {
                "id": "consumer",
                "title_ko": "유저용 · 마음쉼터",
                "status": "live",
                "description_ko": "오늘 마음·타로·대화·마음 돌보기 — 무료 개방(기본)",
                "routes": consumer_routes,
                "hidden_from_consumer": [],
            },
            {
                "id": "license",
                "title_ko": "기관용 · Association License",
                "status": "live",
                "description_ko": "학회 라이선스 · 이론·학자·미술치료 · 표현 도구",
                "routes": license_routes,
                "hidden_from_consumer": ["/theories", "/expressive", "/associations", "/case-notes"],
            },
            {
                "id": "disability",
                "title_ko": disability["title_ko"],
                "status": disability["status"],
                "description_ko": disability["summary_ko"],
                "preview_route": disability["preview_route"],
                "stub_routes": ["/picto", "/disability"],
                "assets": disability["assets"],
                "hidden_from_consumer": ["/picto", "/disability/picto"],
            },
        ],
    }
