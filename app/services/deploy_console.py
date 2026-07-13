"""Deploy console — temporary tunnel status + permanent host options."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_URL_PATH = ROOT / "public-url.json"

RENDER_REPO = "https://github.com/jayhope9907/psychology-tarot-ai"
RENDER_DEPLOY = f"https://render.com/deploy?repo={RENDER_REPO}"
RENDER_LIVE = os.getenv("PUBLIC_BASE_URL", "https://psychology-tarot-ai.onrender.com").rstrip("/")

SHARE_PATHS = [
    ("앱", "/"),
    ("홈", "/home"),
    ("타로", "/tarot"),
    ("AI 대화", "/chat"),
    ("마음 돌보기", "/clinical"),
    ("심리검사", "/psychometrics"),
    ("배포 콘솔", "/deploy"),
]


def _read_public_url_file() -> Optional[Dict[str, Any]]:
    if not PUBLIC_URL_PATH.exists():
        return None
    try:
        data = json.loads(PUBLIC_URL_PATH.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict) and data.get("public_url"):
            return data
    except Exception:
        return None
    return None


def _age_seconds(started_at: Optional[str]) -> Optional[float]:
    if not started_at:
        return None
    try:
        raw = started_at.replace("Z", "+00:00")
        started = datetime.fromisoformat(raw)
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - started).total_seconds())
    except Exception:
        return None


def build_share_links(base: str) -> List[Dict[str, str]]:
    base = (base or "").rstrip("/")
    return [
        {"label_ko": label, "path": path, "url": f"{base}{path}" if base else path}
        for label, path in SHARE_PATHS
    ]


def deploy_status(request_base: Optional[str] = None) -> Dict[str, Any]:
    tunnel = _read_public_url_file()
    tunnel_base = (tunnel or {}).get("public_url") if tunnel else None
    age = _age_seconds((tunnel or {}).get("started_at"))

    local_base = "http://127.0.0.1:8000"
    active_base = request_base or tunnel_base or local_base

    modes = [
        {
            "id": "local",
            "title_ko": "로컬만",
            "kind": "dev",
            "permanent": False,
            "ready": True,
            "url": local_base,
            "note_ko": "이 PC에서만 접속. 외부 공유 불가.",
            "action": {
                "type": "command",
                "label_ko": "로컬 서버 실행",
                "command": "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
            },
        },
        {
            "id": "tunnel",
            "title_ko": "임시 공개 (Cloudflare 터널)",
            "kind": "ephemeral",
            "permanent": False,
            "ready": bool(tunnel_base),
            "url": tunnel_base,
            "started_at": (tunnel or {}).get("started_at"),
            "age_seconds": age,
            "note_ko": "영구 URL이 아닙니다. PC·터널이 켜져 있을 때만 접속됩니다. 재시작하면 주소가 바뀝니다.",
            "action": {
                "type": "command",
                "label_ko": "임시 공개 배포",
                "command": "powershell -ExecutionPolicy Bypass -File scripts/start-public.ps1",
            },
            "stop_command": "powershell -ExecutionPolicy Bypass -File scripts/stop-public.ps1",
        },
        {
            "id": "render",
            "title_ko": "상시 호스팅 (Render)",
            "kind": "hosted",
            "permanent": True,
            "ready": True,
            "url": RENDER_LIVE,
            "note_ko": "무료 플랜은 슬립될 수 있어요. 원클릭으로 Render에 올릴 수 있습니다.",
            "action": {
                "type": "link",
                "label_ko": "Render에 배포하기",
                "href": RENDER_DEPLOY,
            },
        },
    ]

    return {
        "service": "psychology-tarot-ai",
        "console_route": "/deploy",
        "active_base": active_base,
        "local_base": local_base,
        "tunnel": {
            "active": bool(tunnel_base),
            "public_url": tunnel_base,
            "started_at": (tunnel or {}).get("started_at"),
            "age_seconds": age,
            "file": "public-url.json",
            "links": tunnel or {},
        },
        "modes": modes,
        "share_links": build_share_links(active_base if active_base.startswith("http") else local_base),
        "repo": RENDER_REPO,
        "render_deploy": RENDER_DEPLOY,
        "render_live": RENDER_LIVE,
        "hints_ko": [
            "임시 공유: start-public.ps1 실행 → 이 페이지에서 링크 복사",
            "영구가 필요할 때만 Render 원클릭 배포를 쓰세요",
            "터널은 PC가 꺼지거나 스크립트를 멈추면 끊깁니다",
        ],
    }
