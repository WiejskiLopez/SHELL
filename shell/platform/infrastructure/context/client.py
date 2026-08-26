from __future__ import annotations

from typing import Any

import httpx

from shell.platform.application.context.correlation_id import get_correlation_id


class CorrelationIdAsyncClient(httpx.AsyncClient):
    """Async HTTP client that automatically injects the X-Correlation-ID header
    from the current execution context into every outgoing request."""

    def __init__(self, *, service_api_key: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._service_api_key = service_api_key

    async def request(self, method: str, url: httpx.URL | str, **kwargs: Any) -> httpx.Response:
        corr_id = get_correlation_id()
        if corr_id or self._service_api_key:
            headers = kwargs.get("headers", {})
            if headers is None:
                headers = {}
            elif not isinstance(headers, dict):
                headers = dict(headers)
            if corr_id:
                headers.setdefault("X-Correlation-ID", corr_id)
            if self._service_api_key:
                headers.setdefault("X-API-Key", self._service_api_key)
            kwargs["headers"] = headers
        return await super().request(method, url, **kwargs)
