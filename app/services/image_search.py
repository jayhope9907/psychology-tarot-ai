"""웹 사진 검색 — Wikimedia Commons (키 불필요)."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

USER_AGENT = "MaumShelterAI/1.0 (wellness-education; contact=license@maum-shelter.example)"
MAX_RESULTS = 8
ALLOWED_MIME = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"}

IMAGE_SEARCH_HINTS = (
    "사진 검색",
    "이미지 검색",
    "사진 찾아",
    "이미지 찾아",
    "사진 보여",
    "이미지 보여",
    "사진으로 찾아",
    "관련 사진",
    "비슷한 사진",
    "search image",
    "find photos",
    "show pictures",
)


def wants_image_search(message: str, *, explicit: bool = False) -> bool:
    if explicit:
        return True
    text = (message or "").strip().lower()
    if not text:
        return False
    return any(h in text for h in IMAGE_SEARCH_HINTS)


def extract_search_query(message: str) -> str:
    """사용자 문장에서 검색어만 남긴다."""
    text = (message or "").strip()
    if not text:
        return "nature calm"
    cleaned = text
    for hint in IMAGE_SEARCH_HINTS:
        cleaned = re.sub(re.escape(hint), " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[?？!！.。,，]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:120] or text[:80]


def _title_from_filename(name: str) -> str:
    base = re.sub(r"^File:", "", name or "", flags=re.IGNORECASE)
    base = re.sub(r"\.(jpe?g|png|gif|webp|svg)$", "", base, flags=re.IGNORECASE)
    base = base.replace("_", " ").strip()
    return base[:80] or "사진"


async def search_images(query: str, *, limit: int = MAX_RESULTS) -> Dict[str, Any]:
    """Wikimedia Commons에서 공개 이미지를 검색한다."""
    q = (query or "").strip() or "calm nature"
    limit = max(1, min(int(limit or MAX_RESULTS), 12))
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": q,
        "gsrnamespace": "6",
        "gsrlimit": str(limit * 2),
        "prop": "imageinfo",
        "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": "640",
    }
    url = "https://commons.wikimedia.org/w/api.php"
    results: List[Dict[str, Any]] = []
    error: Optional[str] = None

    try:
        async with httpx.AsyncClient(timeout=12.0, headers={"User-Agent": USER_AGENT}) as client:
            res = await client.get(url, params=params)
            res.raise_for_status()
            data = res.json()
    except Exception as exc:  # pragma: no cover - network
        return {
            "query": q,
            "results": [],
            "count": 0,
            "error": str(exc),
            "source": "wikimedia_commons",
        }

    pages = (data.get("query") or {}).get("pages") or {}
    for page in pages.values():
        info_list = page.get("imageinfo") or []
        if not info_list:
            continue
        info = info_list[0]
        mime = (info.get("mime") or "").lower()
        if mime and mime not in ALLOWED_MIME:
            continue
        thumb = info.get("thumburl") or info.get("url")
        full = info.get("url") or thumb
        if not thumb:
            continue
        meta = info.get("extmetadata") or {}
        artist = ""
        if isinstance(meta.get("Artist"), dict):
            artist = re.sub(r"<[^>]+>", "", meta["Artist"].get("value") or "").strip()
        license_short = ""
        if isinstance(meta.get("LicenseShortName"), dict):
            license_short = (meta["LicenseShortName"].get("value") or "").strip()
        title = _title_from_filename(page.get("title") or "")
        results.append(
            {
                "title": title,
                "thumb_url": thumb,
                "url": full,
                "page_url": f"https://commons.wikimedia.org/wiki/{quote(page.get('title') or '', safe=':')}",
                "mime": mime,
                "artist": artist[:80],
                "license": license_short,
                "source": "Wikimedia Commons",
            }
        )
        if len(results) >= limit:
            break

    if not results and not error:
        error = "no_results"

    return {
        "query": q,
        "results": results,
        "count": len(results),
        "error": error,
        "source": "wikimedia_commons",
        "attribution": "Images via Wikimedia Commons (respective licenses)",
    }


def build_image_search_prompt_block(payload: Dict[str, Any]) -> str:
    results = payload.get("results") or []
    query = payload.get("query") or ""
    if not results:
        return (
            f"\n\n사용자가 '{query}' 관련 사진을 검색했지만 결과가 없었습니다. "
            "사과하고, 검색어를 조금 바꿔 보자고 제안하세요. 진단·처방은 하지 마세요."
        )
    lines = [
        f"\n\n사용자가 '{query}'로 사진 검색을 요청했고, 화면에 {len(results)}장의 공개 이미지가 표시됩니다.",
        "사진을 참고해 감정·분위기·연상을 부드럽게 이야기하세요.",
        "이미지를 '진단'하거나 의료적으로 해석하지 마세요. 출처는 Wikimedia Commons입니다.",
        "검색 결과 요약:",
    ]
    for i, item in enumerate(results[:6], 1):
        lines.append(f"{i}. {item.get('title')} — {item.get('url')}")
    return "\n".join(lines)


def validate_image_data_url(data_url: Optional[str], *, max_chars: int = 350_000) -> Optional[str]:
    """data:image/...;base64,... 형식만 허용."""
    if not data_url or not isinstance(data_url, str):
        return None
    text = data_url.strip()
    if len(text) > max_chars:
        return None
    if not text.startswith("data:image/"):
        return None
    if ";base64," not in text:
        return None
    mime = text[len("data:") : text.index(";")]
    if mime.lower() not in ALLOWED_MIME and not mime.lower().startswith("image/"):
        return None
    return text
