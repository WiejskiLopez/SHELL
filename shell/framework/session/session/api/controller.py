from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.application.session.session.commands.delete_session_command import (
    DeleteSessionCommand,
)
from shell.application.session.session.commands.open_session_command import (
    OpenSessionCommand,
)
from shell.application.session.session.commands.update_session_command import (
    UpdateSessionCommand,
)
from shell.application.session.session.queries.list_sessions_query import ListSessionsQuery
from shell.framework.session.session.api.create_session_request import (
    CreateSessionRequest as ApiCreateSessionRequest,
)
from shell.framework.session.session.api.create_session_response import (
    CreateSessionResponse as ApiCreateSessionResponse,
)
from shell.framework.session.session.api.session_response import (
    SessionResponse as ApiSessionResponse,
)
from shell.framework.session.session.api.update_session_request import (
    UpdateSessionRequest as ApiUpdateSessionRequest,
)
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.framework.api.models.page import Page

if TYPE_CHECKING:
    from shell.application.session.session.dto.session import SessionDto
    from shell.application.session.session.ports.session_query_service import (
        SessionQueryService,
    )


def _to_response(dto: SessionDto) -> ApiSessionResponse:
    return ApiSessionResponse(
        id=dto.id,
        goal=dto.goal,
        status=dto.status,
        opened_at=dto.opened_at,
        closed_at=dto.closed_at,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
        deleted_at=dto.deleted_at,
    )


class SessionController:
    __slots__ = ("_command_bus", "_query_bus", "_query_service")

    def __init__(
        self,
        command_bus: CommandBus,
        query_service: SessionQueryService,
        query_bus: QueryBus,
    ) -> None:
        self._command_bus = command_bus
        self._query_service = query_service
        self._query_bus = query_bus

    async def get_session(self, session_id: str) -> ApiSessionResponse:
        result = await self._query_service.get_by_id(session_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
        return _to_response(result)

    async def list_sessions(
        self, page: int = 1, page_size: int = 100, user_id: str | None = None
    ) -> Page[ApiSessionResponse]:
        dtos, total = await self._query_bus.dispatch(
            ListSessionsQuery(page=page, page_size=page_size, user_id=user_id)
        )
        return Page(
            items=[_to_response(dto) for dto in dtos],
            total=total,
            page=page,
            page_size=page_size,
            has_more=(page * page_size) < total,
        )

    async def create_session(self, body: ApiCreateSessionRequest) -> ApiCreateSessionResponse:
        session_id = await self._command_bus.dispatch(OpenSessionCommand(goal=body.goal))
        return ApiCreateSessionResponse(id=str(session_id))

    async def update_session(self, session_id: str, body: ApiUpdateSessionRequest) -> None:
        try:
            await self._command_bus.dispatch(UpdateSessionCommand(session_id=session_id))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def delete_session(self, session_id: str) -> None:
        try:
            await self._command_bus.dispatch(DeleteSessionCommand(session_id=session_id))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
