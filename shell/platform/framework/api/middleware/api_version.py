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

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send

    from shell.platform.framework.api.version import ApiVersionRegistry

API_PATH_PATTERN = re.compile(r"^/api/([^/]+)")


class ApiVersionMiddleware:
    def __init__(self, app: ASGIApp, registry: ApiVersionRegistry) -> None:
        self.app = app
        self._registry = registry

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        version = self._resolve_version(scope)
        scope.setdefault("state", {})["api_version"] = version

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"X-API-Version", version.encode()))

                info = self._registry.get_info(version)
                if info is not None:
                    if info.status == "deprecated" and info.deprecation_date:
                        headers.append(
                            (b"Deprecation", info.deprecation_date.isoformat().encode())
                        )
                    if info.status == "sunset" and info.sunset_date:
                        headers.append(
                            (b"Sunset", info.sunset_date.isoformat().encode())
                        )

                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _resolve_version(self, scope: Scope) -> str:
        path = scope.get("path", "")
        match = API_PATH_PATTERN.match(path)
        if match:
            candidate = match.group(1)
            if self._registry.get_info(candidate) is not None:
                return candidate

        headers = dict(scope.get("headers", []))
        header_version = headers.get(b"x-api-version", b"").decode()
        if header_version and self._registry.get_info(header_version) is not None:
            return header_version

        return self._registry.latest
