"""API version middleware — resolves version and adds RFC 8594 headers.

Resolution priority:
1. URL path:  /api/{version}/...
2. Header:   X-API-Version: {version}
3. Fallback: latest version from registry

Response headers:
- X-API-Version: {resolved_version}
- Deprecation:   {date}  (RFC 8594, gdy status=deprecated)
- Sunset:        {date}  (RFC 8594, gdy status=sunset)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

    from shell.platform.framework.api.version import ApiVersionRegistry

API_PATH_PATTERN = re.compile(r"^/api/([^/]+)")


class ApiVersionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Callable[..., object], registry: ApiVersionRegistry) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._registry = registry

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        version = self._resolve_version(request)
        request.state.api_version = version

        response: Response = await call_next(request)
        response.headers["X-API-Version"] = version

        info = self._registry.get_info(version)
        if info is not None:
            if info.status == "deprecated" and info.deprecation_date:
                response.headers["Deprecation"] = info.deprecation_date.isoformat()
            if info.status == "sunset" and info.sunset_date:
                response.headers["Sunset"] = info.sunset_date.isoformat()

        return response

    def _resolve_version(self, request: Request) -> str:
        match = API_PATH_PATTERN.match(request.url.path)
        if match:
            candidate = match.group(1)
            if self._registry.get_info(candidate) is not None:
                return candidate

        header_version = request.headers.get("X-API-Version")
        if header_version and self._registry.get_info(header_version) is not None:
            return header_version

        return self._registry.latest
