from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware

from shell.platform.application.context.correlation_id import get_correlation_id

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

logger = logging.getLogger("shell.api.audit")


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        logger.info(
            "audit",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_string": str(request.url.query),
                "status": response.status_code,
                "elapsed_ms": round(elapsed * 1000, 2),
                "correlation_id": get_correlation_id(),
                "user_agent": request.headers.get("user-agent", ""),
            },
        )
        return response
