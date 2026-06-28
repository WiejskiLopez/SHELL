"""Correlation-ID middleware — adds X-Correlation-ID header to every request."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.platform.context import (
    reset_correlation_id,
    set_correlation_id,
)
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        cid = request.headers.get("X-Correlation-ID") or ""
        token = set_correlation_id(cid)
        try:
            response: Response = await call_next(request)
            if cid:
                response.headers["X-Correlation-ID"] = cid
            return response
        finally:
            reset_correlation_id(token)
