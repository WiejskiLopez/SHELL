from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from shell.platform.application.context.correlation_id import get_correlation_id

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("shell.api.audit")


class AuditLogMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)

        await self.app(scope, receive, send_wrapper)
        elapsed = time.perf_counter() - start

        logger.info(
            "audit",
            extra={
                "method": scope.get("method", ""),
                "path": scope.get("path", ""),
                "query_string": scope.get("query_string", b"").decode(),
                "status": status_code,
                "elapsed_ms": round(elapsed * 1000, 2),
                "correlation_id": get_correlation_id(),
                "user_agent": _get_header(scope, "user-agent"),
            },
        )


def _get_header(scope: Scope, name: str) -> str:
    headers = dict(scope.get("headers", []))
    return headers.get(name.encode(), b"").decode()
