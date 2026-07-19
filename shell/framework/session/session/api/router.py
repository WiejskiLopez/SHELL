from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from shell.application.execution.session_execution.ports.session_query_service import (
    SessionQueryService,
)
from shell.framework.session.session.api.controller import SessionController
from shell.framework.session.session.api.create_session_request import (
    CreateSessionRequest,
)
from shell.framework.session.session.api.create_session_response import (
    CreateSessionResponse,
)
from shell.framework.session.session.api.session_response import (
    SessionResponse,
)
from shell.framework.session.session.api.update_session_request import (
    UpdateSessionRequest,
)
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.bootstrap.container.core_container import CoreContainer
from shell.platform.framework.api.dependencies import get_core_container

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def get_session_controller(
    container: CoreContainer = Depends(get_core_container),
) -> SessionController:
    try:
        _query_service: SessionQueryService = container.infra.session_query_service
    except Exception:
        raise HTTPException(
            status_code=501, detail="Session query service not implemented"
        ) from None
    command_bus: CommandBus = container.app.buses.command_bus
    return SessionController(command_bus, _query_service)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    controller: SessionController = Depends(get_session_controller),
) -> SessionResponse:
    return await controller.get_session(session_id)


@router.post("/", response_model=CreateSessionResponse, status_code=201)
async def create_session(
    body: CreateSessionRequest,
    controller: SessionController = Depends(get_session_controller),
) -> CreateSessionResponse:
    return await controller.create_session(body)


@router.put("/{session_id}", status_code=204)
async def update_session(
    session_id: str,
    body: UpdateSessionRequest,
    controller: SessionController = Depends(get_session_controller),
) -> None:
    await controller.update_session(session_id, body)


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    controller: SessionController = Depends(get_session_controller),
) -> None:
    await controller.delete_session(session_id)
