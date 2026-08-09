from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from shell.application.user.auth_session.commands.login_auth_session_command import (
    LoginAuthSessionCommand,
)
from shell.application.user.auth_session.commands.logout_auth_session_command import (
    LogoutAuthSessionCommand,
)
from shell.application.user.auth_session.queries.get_current_auth_session_query import (
    GetCurrentAuthSessionQuery,
)
from shell.domain.user.aggregates.auth_session.exceptions.auth_session_login_denied_error import (
    AuthSessionLoginDeniedError,
)
from shell.framework.user.auth_session.api.models import (
    AuthSessionIdResponse,
    CurrentUserResponse,
    LoginAuthSessionRequest,
)
from shell.platform.framework.api.dependencies import get_core_container

if TYPE_CHECKING:
    from shell.platform.application.bus.command_bus import CommandBus
    from shell.platform.application.bus.query_bus import QueryBus
    from shell.platform.bootstrap.container.core_container import CoreContainer

router = APIRouter(prefix="/auth_session", tags=["AuthSessions"])
SESSION_COOKIE_NAME = "shell_session"
SESSION_COOKIE_MAX_AGE = 24 * 60 * 60


def _buses(container: CoreContainer) -> tuple[CommandBus, QueryBus]:
    return container.app.buses.command_bus, container.app.buses.query_bus


@router.post("/login", response_model=AuthSessionIdResponse)
async def login_auth_session(
    body: LoginAuthSessionRequest,
    response: Response,
    container: CoreContainer = Depends(get_core_container),
) -> AuthSessionIdResponse:
    command_bus, _ = _buses(container)
    try:
        result = await command_bus.dispatch(LoginAuthSessionCommand(email=body.email))
    except AuthSessionLoginDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from exc

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=result.token,
        httponly=True,
        max_age=SESSION_COOKIE_MAX_AGE,
        samesite="lax",
        secure=False,
    )
    return AuthSessionIdResponse(id=result.auth_session_id)


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user(
    request: Request,
    container: CoreContainer = Depends(get_core_container),
) -> CurrentUserResponse:
    _, query_bus = _buses(container)
    auth_session = await query_bus.dispatch(
        GetCurrentAuthSessionQuery(token=request.cookies.get(SESSION_COOKIE_NAME, ""))
    )
    if auth_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthenticated",
        )
    return CurrentUserResponse(user_id=auth_session.user_id)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_auth_session(
    request: Request,
    response: Response,
    container: CoreContainer = Depends(get_core_container),
) -> None:
    command_bus, _ = _buses(container)
    await command_bus.dispatch(
        LogoutAuthSessionCommand(token=request.cookies.get(SESSION_COOKIE_NAME, ""))
    )
    response.delete_cookie(key=SESSION_COOKIE_NAME)
