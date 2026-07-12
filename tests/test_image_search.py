"""사진 검색 · 첨부 검증 테스트."""
from __future__ import annotations

import asyncio

from app.services.image_search import (
    extract_search_query,
    validate_image_data_url,
    wants_image_search,
)


def test_wants_image_search_keywords():
    assert wants_image_search("바다 사진 검색해줘")
    assert wants_image_search("조용한 숲 이미지 찾아줘")
    assert wants_image_search("hello", explicit=True)
    assert not wants_image_search("오늘 기분이 안 좋아요")


def test_extract_search_query_strips_hints():
    assert "바다" in extract_search_query("바다 사진 검색")
    assert "사진 검색" not in extract_search_query("바다 사진 검색")


def test_validate_image_data_url():
    ok = "data:image/jpeg;base64,/9j/4AAQ"
    assert validate_image_data_url(ok) == ok
    assert validate_image_data_url("https://example.com/a.jpg") is None
    assert validate_image_data_url("data:text/plain;base64,abc") is None
    assert validate_image_data_url("data:image/png;base64," + ("a" * 400_000)) is None


def test_search_images_mocked(monkeypatch):
    from app.services import image_search as mod

    class FakeResp:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "query": {
                    "pages": {
                        "1": {
                            "title": "File:Calm_lake.jpg",
                            "imageinfo": [
                                {
                                    "mime": "image/jpeg",
                                    "thumburl": "https://example.com/thumb.jpg",
                                    "url": "https://example.com/full.jpg",
                                    "extmetadata": {
                                        "Artist": {"value": "Test"},
                                        "LicenseShortName": {"value": "CC BY-SA 4.0"},
                                    },
                                }
                            ],
                        }
                    }
                }
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url, params=None):
            return FakeResp()

    monkeypatch.setattr(mod.httpx, "AsyncClient", FakeClient)
    payload = asyncio.run(mod.search_images("calm lake", limit=4))
    assert payload["count"] == 1
    assert payload["results"][0]["title"] == "Calm lake"
    assert "thumb.jpg" in payload["results"][0]["thumb_url"]


def test_run_chat_turn_emits_image_results(monkeypatch):
    from app.db.database import reset_db
    from app.services.chat_session import ChatSessionState
    from app.services.chat_stream import run_chat_turn

    reset_db()

    async def fake_search(query, limit=8):
        return {
            "query": query,
            "results": [
                {
                    "title": "Forest",
                    "thumb_url": "https://example.com/f.jpg",
                    "url": "https://example.com/f.jpg",
                    "page_url": "https://commons.wikimedia.org/wiki/File:Forest.jpg",
                    "source": "Wikimedia Commons",
                }
            ],
            "count": 1,
            "source": "wikimedia_commons",
        }

    monkeypatch.setattr("app.services.image_search.search_images", fake_search)

    async def fake_stream(*args, **kwargs):
        yield "사진을 함께 봤어요. "

    async def collect():
        state = ChatSessionState(user_id="u-img", session_id="s-img")
        events = []
        async for event in run_chat_turn(
            state,
            "숲 사진 검색해줘",
            client=None,
            stream_fn=fake_stream,
            image_search=True,
        ):
            events.append(event)
        return events

    events = asyncio.run(collect())
    kinds = [e["event"] for e in events]
    assert "image_results" in kinds
    assert "token" in kinds
    assert "done" in kinds
    img = next(e for e in events if e["event"] == "image_results")
    assert img["data"]["count"] == 1
