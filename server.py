"""Vercel ASGI entrypoint — re-exports FastAPI `app` with import-failure diagnostics."""
from __future__ import annotations

try:
    from app.main import app as app
except Exception as exc:  # pragma: no cover
    import traceback

    from fastapi import FastAPI
    from fastapi.responses import JSONResponse, PlainTextResponse

    _error = str(exc)
    _error_type = type(exc).__name__
    _tb_lines = traceback.format_exc().splitlines()[-30:]
    app = FastAPI(title="Psychology Tarot AI boot error")

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
    async def _boot_error(full_path: str = ""):
        payload = {
            "ok": False,
            "error": _error,
            "error_type": _error_type,
            "traceback": _tb_lines,
            "path": full_path,
        }
        text = f"BOOT_ERROR={_error_type}: {_error}\n" + "\n".join(_tb_lines)
        if full_path in {"", "health", "boot-error"} or full_path.endswith(".txt"):
            return PlainTextResponse(text, status_code=500)
        return JSONResponse(payload, status_code=500)


handler = app
