"""장애인용(그림마음·AAC) 별도 제품 — 자산 매니페스트.

일반 유저 앱에서는 UI 진입점을 숨기고, 코드·API는 유지한다.
"""
from __future__ import annotations

from typing import Any, Dict, List


def disability_product_manifest() -> Dict[str, Any]:
    """보관 중인 장애인용 제품 표면 목록."""
    assets: List[Dict[str, str]] = [
        {"kind": "ui_stub", "path": "/picto", "file": "static/disability-coming-soon.html"},
        {"kind": "ui_stub", "path": "/disability", "file": "static/disability-coming-soon.html"},
        {"kind": "ui_app", "path": "/disability/picto", "file": "static/picto.html"},
        {"kind": "js", "path": "/static/js/picto-scene.js", "file": "static/js/picto-scene.js"},
        {"kind": "bundle", "path": "/static/picto-catalog.bundle.json", "file": "static/picto-catalog.bundle.json"},
        {"kind": "service", "path": "picto_vocabulary", "file": "app/services/picto_vocabulary.py"},
        {"kind": "docs", "path": "docs/disability-product.md", "file": "docs/disability-product.md"},
        {"kind": "api", "path": "/api/v1/picto/*", "file": "app/main.py"},
        {"kind": "tests", "path": "tests/test_picto.py", "file": "tests/test_picto.py"},
    ]
    return {
        "product": "disability_accessibility",
        "status": "deferred_separate_product",
        "title_ko": "장애인용 · 그림마음 (AAC)",
        "summary_ko": (
            "유저용 앱과 분리해 별도 제품으로 준비합니다. "
            "그림마음 UI·어휘·API는 삭제하지 않고 보관합니다."
        ),
        "user_app_exposed": False,
        "preview_route": "/disability/picto",
        "assets": assets,
    }
