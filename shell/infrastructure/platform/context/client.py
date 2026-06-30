from __future__ import annotations

from typing import Any

import httpx

from shell.application.platform.context.correlation_id import get_correlation_id


class CorrelationIdAsyncClient(httpx.AsyncClient):
    """Async HTTP client that automatically injects the X-Correlation-ID header
    from the current execution context into every outgoing request."""

    async def request(self, method: str, url: httpx.URL | str, **kwargs: Any) -> httpx.Response:
        corr_id = get_correlation_id()
        if corr_id:
            headers = kwargs.get("headers", {})
            if not isinstance(headers, dict):
                headers = dict(headers)
            headers.setdefault("X-Correlation-ID", corr_id)
            kwargs["headers"] = headers
        return await super().request(method, url, **kwargs)
