from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request as _Request

from shell.application.session.dto.session import SessionDto

if TYPE_CHECKING:
    from shell.application.execution.ports.queries.session_query_service import (
        SessionQueryService,
    )
    from shell.bootstrap.platform.container.core_container import CoreContainer

router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container


def get_session_query_service(
    container: CoreContainer = Depends(get_core_container),
) -> SessionQueryService:
    return container.infra.session_query_service()


@router.get("/{session_id}/history", response_model=SessionDto)
async def get_session_history(
    session_id: str,
    query_service: SessionQueryService = Depends(get_session_query_service),
) -> SessionDto | None:
    result = await query_service.get_session_history(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return result
