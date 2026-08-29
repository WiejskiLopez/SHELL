from __future__ import annotations

import time
from datetime import UTC, datetime
from http.cookies import SimpleCookie
from typing import TYPE_CHECKING, Protocol, cast

import jwt
from starlette.responses import JSONResponse

from shell.platform.application.authentication.request_signing import (
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    verify_signature,
)
from shell.platform.application.context.correlation_id import get_correlation_id
from shell.platform.framework.api.models.problem_detail import ProblemDetail
from shell.platform.framework.api.principal import (
    SYSTEM_SUBJECT_ID,
    Principal,
    PrincipalKind,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Collection

    from starlette.types import ASGIApp, Receive, Scope, Send


class _QueryBus(Protocol):
    async def dispatch(self, query: object) -> object: ...


class AuthMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        api_key: str = "",
        jwt_secret: str = "",
        session_query_factory: Callable[[str], object] | None = None,
        public_exact: Collection[str] | None = None,
        public_prefix: Collection[str] | None = None,
        signature_max_age_seconds: int = 300,
    ) -> None:
        self.app = app
        self._api_key = api_key
        self._jwt_secret = jwt_secret
        self._session_query_factory = session_query_factory
        self._public_exact = frozenset(public_exact or ())
        self._public_prefix = frozenset(public_prefix or ())
        self._signature_max_age_seconds = signature_max_age_seconds

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if self._is_public_path(path):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        principal = await self._resolve_principal(scope, headers)
        if principal is None:
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

        scope.setdefault("state", {})["principal"] = principal
        await self.app(scope, receive, send)

    def _is_public_path(self, path: str) -> bool:
        if path in self._public_exact:
            return True
        return any(path.startswith(prefix) for prefix in self._public_prefix)

    async def _resolve_principal(
        self, scope: Scope, headers: dict[bytes, bytes]
    ) -> Principal | None:
        session_token = self._session_token(headers)
        if session_token:
            query_bus = self._query_bus(scope)
            if query_bus is not None and self._session_query_factory is not None:
                session = await query_bus.dispatch(self._session_query_factory(session_token))
                if session is not None and hasattr(session, "user_id"):
                    return Principal(session.user_id, PrincipalKind.USER)

        auth = headers.get(b"authorization", b"").decode()
        if auth.startswith("Bearer "):
            token = auth[7:]
            subject_id = await self._validate_jwt(token)
            if subject_id is not None:
                return Principal(subject_id, PrincipalKind.USER)

        api_key = headers.get(b"x-api-key", b"").decode()
        if api_key and api_key == self._api_key:
            return Principal(SYSTEM_SUBJECT_ID, PrincipalKind.SYSTEM)

        method = str(scope.get("method", "GET")).upper()
        path = str(scope.get("path", ""))
        if self._is_valid_signature(headers, method=method, path=path):
            return Principal(SYSTEM_SUBJECT_ID, PrincipalKind.SYSTEM)

        return None

    def _is_valid_signature(
        self,
        headers: dict[bytes, bytes],
        *,
        method: str,
        path: str,
    ) -> bool:
        if not self._api_key:
            return False
        signature = headers.get(SIGNATURE_HEADER.lower().encode("ascii"), b"").decode()
        if not signature:
            return False
        timestamp_raw = headers.get(TIMESTAMP_HEADER.lower().encode("ascii"), b"").decode()
        if not timestamp_raw.isdigit():
            return False
        timestamp = int(timestamp_raw)
        return verify_signature(
            secret=self._api_key,
            method=method,
            path=path,
            timestamp=timestamp,
            signature=signature,
            now=int(time.time()),
            max_age_seconds=self._signature_max_age_seconds,
        )

    async def _resolve_user(self, scope: Scope, headers: dict[bytes, bytes]) -> str | None:
        principal = await self._resolve_principal(scope, headers)
        return principal.subject_id if principal is not None else None

    @staticmethod
    def _session_token(headers: dict[bytes, bytes]) -> str | None:
        cookie_header = headers.get(b"cookie", b"").decode()
        cookies = SimpleCookie()
        cookies.load(cookie_header)
        morsel = cookies.get("shell_session")
        return morsel.value if morsel is not None and morsel.value else None

    @staticmethod
    def _query_bus(scope: Scope) -> _QueryBus | None:
        app = scope.get("app")
        state = getattr(app, "state", None)
        container = getattr(state, "core_container", None)
        application = getattr(container, "app", None)
        buses = getattr(application, "buses", None)
        query_bus = getattr(buses, "query_bus", None)
        if query_bus is None:
            query_bus = getattr(container, "query_bus", None)
        if query_bus is not None and not hasattr(query_bus, "dispatch") and callable(query_bus):
            query_bus = query_bus()
        return cast("_QueryBus | None", query_bus)

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
