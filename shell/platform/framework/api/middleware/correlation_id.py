"""Correlation-ID middleware — adds X-Correlation-ID header to every request."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.application.context import (
    reset_correlation_id,
    set_correlation_id,
)

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send


class CorrelationIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers: dict[bytes, bytes] = dict(scope.get("headers", []))
        cid = headers.get(b"x-correlation-id", b"").decode()
        token = set_correlation_id(cid)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start" and cid:
                message["headers"] = list(message.get("headers", [])) + [
                    (b"X-Correlation-ID", cid.encode())
                ]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            reset_correlation_id(token)
