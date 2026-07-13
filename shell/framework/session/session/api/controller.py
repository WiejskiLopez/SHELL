from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.framework.session.session.api.session_response import SessionResponse

if TYPE_CHECKING:
    from shell.application.execution.session_execution.ports.session_query_service import (
        SessionQueryService,
    )
    from shell.application.session.session.dto.session import SessionDto


def _to_response(dto: SessionDto) -> SessionResponse:
    return SessionResponse(
        id=dto.id,
        goal=dto.goal,
        status=dto.status,
        opened_at=dto.opened_at,
        closed_at=dto.closed_at,
    )


class SessionController:
    __slots__ = ("_query_service",)

    def __init__(self, query_service: SessionQueryService) -> None:
        self._query_service = query_service

    async def get_by_id(self, session_id: str) -> SessionResponse:
        result = await self._query_service.get_by_id(session_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
        return _to_response(result)
