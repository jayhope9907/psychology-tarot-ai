"""Vercel ASGI entrypoint with import-error diagnostics."""
from __future__ import annotations

try:
    from app.main import app as app
except Exception as exc:  # pragma: no cover - production boot diagnostics only
    import traceback

    from fastapi import FastAPI
    from fastapi.responses import JSONResponse, PlainTextResponse

    _error = str(exc)
    _tb = traceback.format_exc()
    app = FastAPI(title="Psychology Tarot AI boot error")

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
    async def _boot_error(full_path: str = ""):
        payload = {
            "ok": False,
            "error": _error,
            "error_type": type(exc).__name__,
            "traceback": _tb.splitlines()[-20:],
        }
        if full_path.endswith(".txt") or full_path == "health":
            return PlainTextResponse(
                f"BOOT_ERROR={type(exc).__name__}: {_error}\n" + "\n".join(payload["traceback"]),
                status_code=500,
            )
        return JSONResponse(payload, status_code=500)


handler = app
