from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from shell.framework.session.session.api.controller import SessionController
from shell.framework.session.session.api.session_response import SessionResponse
from shell.platform.framework.api.dependencies import get_core_container

if TYPE_CHECKING:
    from shell.application.execution.session_execution.ports.session_query_service import (
        SessionQueryService,
    )
    from shell.platform.bootstrap.container.core_container import CoreContainer

router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_session_controller(
    container: CoreContainer = Depends(get_core_container),
) -> SessionController:
    query_service: SessionQueryService = container.infra.session_query_service()
    return SessionController(query_service)


@router.get("/{session_id}/history", response_model=SessionResponse)
async def get_session_history(
    session_id: str,
    controller: SessionController = Depends(get_session_controller),
) -> SessionResponse:
    return await controller.get_by_id(session_id)
