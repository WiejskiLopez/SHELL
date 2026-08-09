from __future__ import annotations

from datetime import UTC, datetime
from http.cookies import SimpleCookie
from typing import TYPE_CHECKING

import jwt
from starlette.responses import JSONResponse

from shell.application.user.auth_session.queries.get_current_auth_session_query import (
    GetCurrentAuthSessionQuery,
)
from shell.platform.application.context.correlation_id import get_correlation_id
from shell.platform.framework.api.models.problem_detail import ProblemDetail

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send

PUBLIC_EXACT = frozenset(
    {
        "/health",
        "/api",
        "/api/v1/users/by-email",
        "/api/v1/auth_session/login",
        "/api/v1/auth_session/me",
        "/api/v1/auth_session/logout",
    }
)
PUBLIC_PREFIX = frozenset({"/docs", "/redoc", "/openapi.json"})


class AuthMiddleware:
    def __init__(self, app: ASGIApp, api_key: str = "", jwt_secret: str = "") -> None:
        self.app = app
        self._api_key = api_key
        self._jwt_secret = jwt_secret

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if self._is_public_path(path):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        user_id = await self._resolve_user(scope, headers)
        if user_id is None:
            problem = ProblemDetail(
                title="Unauthorized",
                status=401,
                detail="Missing or invalid authentication",
                instance=path,
                correlation_id=get_correlation_id(),
                timestamp=datetime.now(UTC).isoformat(),
            )
            response = JSONResponse(status_code=401, content=problem.model_dump(mode="json"))
            await response(scope, receive, send)
            return

        scope.setdefault("state", {})["current_user_id"] = user_id
        await self.app(scope, receive, send)

    def _is_public_path(self, path: str) -> bool:
        if path in PUBLIC_EXACT:
            return True
        return any(path.startswith(prefix) for prefix in PUBLIC_PREFIX)

    async def _resolve_user(self, scope: Scope, headers: dict[bytes, bytes]) -> str | None:
        session_token = self._session_token(headers)
        if session_token:
            query_bus = self._query_bus(scope)
            if query_bus is not None:
                session = await query_bus.dispatch(
                    GetCurrentAuthSessionQuery(token=session_token)
                )
                if session is not None:
                    return session.user_id

        auth = headers.get(b"authorization", b"").decode()
        if auth.startswith("Bearer "):
            token = auth[7:]
            return await self._validate_jwt(token)

        api_key = headers.get(b"x-api-key", b"").decode()
        if api_key and api_key == self._api_key:
            return "system"

        return None

    @staticmethod
    def _session_token(headers: dict[bytes, bytes]) -> str | None:
        cookie_header = headers.get(b"cookie", b"").decode()
        cookies = SimpleCookie()
        cookies.load(cookie_header)
        morsel = cookies.get("shell_session")
        return morsel.value if morsel is not None and morsel.value else None

    @staticmethod
    def _query_bus(scope: Scope) -> object | None:
        app = scope.get("app")
        state = getattr(app, "state", None)
        container = getattr(state, "core_container", None)
        application = getattr(container, "app", None)
        buses = getattr(application, "buses", None)
        return getattr(buses, "query_bus", None)

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
