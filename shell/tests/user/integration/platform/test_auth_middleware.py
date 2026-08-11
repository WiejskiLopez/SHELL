from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from shell.platform.framework.api.middleware.api_key import AuthMiddleware
from shell.platform.framework.api.principal import Principal, PrincipalKind
from shell.user.application.user.auth_session.dto.current_auth_session import CurrentAuthSessionDto
from shell.user.application.user.auth_session.queries.get_current_auth_session_query import (
    GetCurrentAuthSessionQuery,
)

if TYPE_CHECKING:
    from starlette.types import ASGIApp


class _QueryBus:
    def __init__(self, result: CurrentAuthSessionDto | None) -> None:
        self.result = result
        self.query: GetCurrentAuthSessionQuery | None = None

    async def dispatch(self, query: GetCurrentAuthSessionQuery) -> CurrentAuthSessionDto | None:
        self.query = query
        return self.result


def _scope(query_bus: _QueryBus) -> dict[str, object]:
    return {
        "type": "http",
        "app": SimpleNamespace(
            state=SimpleNamespace(
                core_container=SimpleNamespace(
                    app=SimpleNamespace(buses=SimpleNamespace(query_bus=query_bus))
                )
            )
        ),
    }


@pytest.mark.asyncio
async def test_session_cookie_resolves_current_user() -> None:
    query_bus = _QueryBus(CurrentAuthSessionDto(auth_session_id="session-1", user_id="user-1"))
    middleware = AuthMiddleware(
        app=cast("ASGIApp", SimpleNamespace()),
        api_key="system-key",
        session_query_factory=lambda token: GetCurrentAuthSessionQuery(token=token),
    )

    principal = await middleware._resolve_principal(
        _scope(query_bus),
        {b"cookie": b"shell_session=raw-token"},
    )

    assert principal == Principal(subject_id="user-1", kind=PrincipalKind.USER)
    assert query_bus.query == GetCurrentAuthSessionQuery(token="raw-token")


@pytest.mark.asyncio
async def test_invalid_session_cookie_does_not_authenticate_request() -> None:
    query_bus = _QueryBus(None)
    middleware = AuthMiddleware(
        app=cast("ASGIApp", SimpleNamespace()),
        api_key="system-key",
        session_query_factory=lambda token: GetCurrentAuthSessionQuery(token=token),
    )

    principal = await middleware._resolve_principal(
        _scope(query_bus),
        {b"cookie": b"shell_session=expired-token"},
    )

    assert principal is None


@pytest.mark.asyncio
async def test_api_key_resolves_system_principal() -> None:
    middleware = AuthMiddleware(app=cast("ASGIApp", SimpleNamespace()), api_key="system-key")

    principal = await middleware._resolve_principal(
        _scope(_QueryBus(None)),
        {b"x-api-key": b"system-key"},
    )

    assert principal == Principal(subject_id="system", kind=PrincipalKind.SYSTEM)
