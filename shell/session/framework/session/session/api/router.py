from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.framework.api.dependencies import (
    ContainerProtocol,
    get_core_container,
)
from shell.platform.framework.api.models.page import Page
from shell.platform.framework.api.principal import (
    Principal,
    get_principal,
    require_user_principal,
)
from shell.session.application.session.session.ports.session_query_service import (
    SessionQueryService,
)
from shell.session.framework.session.session.api.controller import SessionController
from shell.session.framework.session.session.api.create_session_request import (
    CreateSessionRequest,
)
from shell.session.framework.session.session.api.create_session_response import (
    CreateSessionResponse,
)
from shell.session.framework.session.session.api.session_response import (
    SessionResponse,
)
from shell.session.framework.session.session.api.update_session_request import (
    UpdateSessionRequest,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def get_session_controller(
    container: ContainerProtocol = Depends(get_core_container),
) -> SessionController:
    try:
        _query_service: SessionQueryService = (
            container.infra.session_query_service
            if hasattr(container, "app")
            else container.session_query_service()
        )
    except Exception:
        raise HTTPException(
            status_code=501, detail="Session query service not implemented"
        ) from None
    command_bus: CommandBus = (
        container.app.buses.command_bus
        if hasattr(container, "app")
        else container.command_bus()
    )
    query_bus: QueryBus = (
        container.app.buses.query_bus
        if hasattr(container, "app")
        else container.query_bus()
    )
    return SessionController(command_bus, _query_service, query_bus)


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
async def update_session(
    session_id: str,
    body: UpdateSessionRequest,
    principal: Principal = Depends(get_principal),
    controller: SessionController = Depends(get_session_controller),
) -> None:
    await controller.update_session(session_id, body, principal=principal)


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    principal: Principal = Depends(get_principal),
    controller: SessionController = Depends(get_session_controller),
) -> None:
    await controller.delete_session(session_id, principal=principal)
