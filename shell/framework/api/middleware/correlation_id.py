"""Correlation-ID middleware — adds X-Correlation-ID header to every request."""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        cid = request.headers.get("X-Correlation-ID") or ""
        token = correlation_id_var.set(cid)
        try:
            response: Response = await call_next(request)
            if cid:
                response.headers["X-Correlation-ID"] = cid
            return response
        finally:
            correlation_id_var.reset(token)
