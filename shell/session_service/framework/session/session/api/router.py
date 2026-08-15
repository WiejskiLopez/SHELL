from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.framework.api.dependencies import get_command_bus, get_query_bus
from shell.platform.framework.api.models.page import Page
from shell.platform.framework.api.principal import (
    Principal,
    get_principal,
    require_user_principal,
)
from shell.session_service.framework.session.session.api.change_session_request import (
    ChangeSessionRequest,
)
from shell.session_service.framework.session.session.api.controller import SessionController
from shell.session_service.framework.session.session.api.create_session_request import (
    CreateSessionRequest,
)
from shell.session_service.framework.session.session.api.create_session_response import (
    CreateSessionResponse,
)
from shell.session_service.framework.session.session.api.session_response import (
    SessionResponse,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def get_session_controller(
    command_bus: CommandBus = Depends(get_command_bus),
    query_bus: QueryBus = Depends(get_query_bus),
) -> SessionController:
    return SessionController(command_bus, query_bus)


@router.get("", response_model=Page[SessionResponse])
async def list_sessions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=1000, alias="page_size"),
    user_id: str | None = Query(default=None),
    principal: Principal = Depends(get_principal),
    controller: SessionController = Depends(get_session_controller),
) -> Page[SessionResponse]:
    return await controller.list_sessions(
        page=page,
        page_size=page_size,
        user_id=user_id,
        principal=principal,
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    principal: Principal = Depends(get_principal),
    controller: SessionController = Depends(get_session_controller),
) -> SessionResponse:
    return await controller.get_session(session_id, principal=principal)


@router.post("/", response_model=CreateSessionResponse, status_code=201)
async def create_session(
    body: CreateSessionRequest,
    principal: Principal = Depends(require_user_principal),
    controller: SessionController = Depends(get_session_controller),
) -> CreateSessionResponse:
    return await controller.create_session(body, user_id=principal.subject_id)


@router.put("/{session_id}", status_code=204)
async def change_session(
    session_id: str,
    body: ChangeSessionRequest,
    principal: Principal = Depends(get_principal),
    controller: SessionController = Depends(get_session_controller),
) -> None:
    await controller.change_session(session_id, body, principal=principal)


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    principal: Principal = Depends(get_principal),
    controller: SessionController = Depends(get_session_controller),
) -> None:
    await controller.delete_session(session_id, principal=principal)
