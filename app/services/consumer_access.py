"""유저(소비자) 앱 접근 정책 — 라이선스·구독은 별도 B2B 제품으로 분리."""
from __future__ import annotations

import os

# 기본: 유저용은 결제·라이선스 없이 전체 개방. 기관용은 추후 별도 배포.
CONSUMER_OPEN_ACCESS = os.getenv("CONSUMER_OPEN_ACCESS", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

B2B_SEPARATE_NOTE_KO = (
    "학회 라이선스·구독·케이스 노트(기관용)는 유저 앱과 분리해 따로 준비합니다."
)


def consumer_open() -> bool:
    return CONSUMER_OPEN_ACCESS


def unlock_session_for_consumer(session) -> None:
    """세션을 유저용으로 개방: 결제 완료 취급, 라이선스 바인딩 제거."""
    if not consumer_open():
        return
    session.assessment_paid = True
    if not session.assessment_package:
        session.assessment_package = {
            "tier_id": "open",
            "title_ko": "마음 탐색 (무료)",
            "payment_required": False,
            "price_krw": 0,
            "consumer_open": True,
        }
    else:
        session.assessment_package = dict(session.assessment_package)
        session.assessment_package["payment_required"] = False
        session.assessment_package["price_krw"] = 0
        session.assessment_package["consumer_open"] = True
    # 유저 앱에서는 기관 라이선스 필터를 적용하지 않음
    session.org_entitlements = None
    session.org_id = None
    session.org_name = None
    session.association_license = None
