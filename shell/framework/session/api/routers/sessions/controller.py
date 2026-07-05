from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

if TYPE_CHECKING:
    from shell.application.execution.ports.queries.session_query_service import (
        SessionQueryService,
    )
    from shell.application.session.dto.session import SessionDto


class SessionController:
    __slots__ = ("_query_service",)

    def __init__(self, query_service: SessionQueryService) -> None:
        self._query_service = query_service

    async def get_session_history(self, session_id: str) -> SessionDto:
        result = await self._query_service.get_session_history(session_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
        return result
