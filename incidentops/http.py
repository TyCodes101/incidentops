"""Bound write bodies before buffering, independently of an ingress proxy."""

import os

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


def security_headers():
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "same-origin",
        "Cache-Control": "no-store",
    }
    if os.getenv("APP_ENV") == "production":
        headers["Strict-Transport-Security"] = "max-age=31536000"
    return headers


class RequestSizeLimit:
    def __init__(self, app: ASGIApp, limit: int = 65536):
        self.app = app
        self.limit = limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or scope["method"] in {"GET", "HEAD", "OPTIONS"}:
            return await self.app(scope, receive, send)
        too_large = JSONResponse(
            {"detail": "Request too large"}, status_code=413, headers=security_headers()
        )
        headers = dict(scope.get("headers", []))
        # Content-Length is only an early rejection hint; actual bytes are counted too.
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared = 0
        if declared > self.limit:
            return await too_large(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > self.limit:
                return await too_large(scope, receive, send)
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        pending = True

        async def replay() -> Message:
            nonlocal pending
            if pending:
                pending = False
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)
