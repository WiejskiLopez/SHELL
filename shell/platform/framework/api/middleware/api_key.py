from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import jwt
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from shell.platform.application.context.correlation_id import get_correlation_id
from shell.platform.framework.api.models.problem_detail import ProblemDetail

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

PUBLIC_EXACT = frozenset({"/health", "/api"})
PUBLIC_PREFIX = frozenset({"/docs", "/redoc", "/openapi.json"})


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Callable, api_key: str = "", jwt_secret: str = "") -> None:
        super().__init__(app)
        self._api_key = api_key
        self._jwt_secret = jwt_secret

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self._is_public_path(request.url.path):
            return await call_next(request)

        user_id = await self._resolve_user(request)
        if user_id is None:
            problem = ProblemDetail(
                title="Unauthorized",
                status=401,
                detail="Missing or invalid authentication",
                instance=str(request.url.path),
                correlation_id=get_correlation_id(),
                timestamp=datetime.now(UTC).isoformat(),
            )
            return JSONResponse(status_code=401, content=problem.model_dump(mode="json"))

        request.state.current_user_id = user_id
        return await call_next(request)

    def _is_public_path(self, path: str) -> bool:
        if path in PUBLIC_EXACT:
            return True
        return any(path.startswith(prefix) for prefix in PUBLIC_PREFIX)

    async def _resolve_user(self, request: Request) -> str | None:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            return await self._validate_jwt(token)

        api_key = request.headers.get("X-API-Key", "")
        if api_key and api_key == self._api_key:
            return "system"

        return None

    async def _validate_jwt(self, token: str) -> str | None:
        if not self._jwt_secret:
            return None
        try:
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=["HS256"],
                options={"require": ["exp", "sub"]},
            )
            return payload.get("sub")
        except jwt.PyJWTError:
            return None
