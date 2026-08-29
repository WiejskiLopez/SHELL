from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.framework.api.models.page import Page
from shell.platform.framework.api.principal import Principal, PrincipalKind
from shell.session_service.application.session.session.commands.change_session_command import (
    ChangeSessionCommand,
)
from shell.session_service.application.session.session.commands.delete_session_command import (
    DeleteSessionCommand,
)
from shell.session_service.application.session.session.commands.open_session_command import (
    OpenSessionCommand,
)
from shell.session_service.application.session.session.exceptions.session_not_found_error import (
    SessionNotFoundError,
)
from shell.session_service.application.session.session.queries.get_session_by_id_query import (
    GetSessionByIdQuery,
)
from shell.session_service.application.session.session.queries.list_sessions_query import (
    ListSessionsQuery,
)
from shell.session_service.framework.session.session.api.change_session_request import (
    ChangeSessionRequest as ApiChangeSessionRequest,
)
from shell.session_service.framework.session.session.api.create_session_request import (
    CreateSessionRequest as ApiCreateSessionRequest,
)
from shell.session_service.framework.session.session.api.create_session_response import (
    CreateSessionResponse as ApiCreateSessionResponse,
)
from shell.session_service.framework.session.session.api.session_response import (
    SessionResponse as ApiSessionResponse,
)

if TYPE_CHECKING:
    from shell.session_service.application.session.session.dto.session import SessionDto


def _to_response(dto: SessionDto) -> ApiSessionResponse:
    return ApiSessionResponse(
        id=dto.id,
        user_id=dto.user_id,
        status=dto.status,
        opened_at=dto.opened_at,
        closed_at=dto.closed_at,
        created_at=dto.created_at,
        changed_at=dto.changed_at,
        deleted_at=dto.deleted_at,
    )


class SessionController:
    __slots__ = ("_command_bus", "_query_bus")

    def __init__(
        self,
        command_bus: CommandBus,
        query_bus: QueryBus,
    ) -> None:
        self._command_bus = command_bus
        self._query_bus = query_bus

    async def get_session(self, session_id: str, principal: Principal) -> ApiSessionResponse:
        result = await self._query_bus.dispatch(GetSessionByIdQuery(session_id=session_id))
        if result is None:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
        self._require_owner(result.user_id, principal, session_id)
        return _to_response(result)

    async def list_sessions(
        self,
        page: int = 1,
        page_size: int = 100,
        user_id: str | None = None,
        principal: Principal | None = None,
    ) -> Page[ApiSessionResponse]:
        if principal is None:
            raise HTTPException(status_code=401, detail="Missing or invalid authentication")
        scoped_user_id = user_id if principal.kind == PrincipalKind.SYSTEM else principal.subject_id
        dtos, total = await self._query_bus.dispatch(
            ListSessionsQuery(page=page, page_size=page_size, user_id=scoped_user_id)
        )
        return Page(
            items=[_to_response(dto) for dto in dtos],
            total=total,
            page=page,
            page_size=page_size,
            has_more=(page * page_size) < total,
        )

    async def create_session(
        self, body: ApiCreateSessionRequest, user_id: str
    ) -> ApiCreateSessionResponse:
        session_id = await self._command_bus.dispatch(OpenSessionCommand(user_id=user_id))
        return ApiCreateSessionResponse(id=str(session_id))

    async def change_session(
        self, session_id: str, body: ApiChangeSessionRequest, principal: Principal
    ) -> None:
        try:
            session = await self._query_bus.dispatch(GetSessionByIdQuery(session_id=session_id))
            if session is None:
                raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
            self._require_owner(session.user_id, principal, session_id)
            await self._command_bus.dispatch(ChangeSessionCommand(session_id=session_id))
        except HTTPException:
            raise
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    async def delete_session(self, session_id: str, principal: Principal) -> None:
        try:
            session = await self._query_bus.dispatch(GetSessionByIdQuery(session_id=session_id))
            if session is None:
                raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
            self._require_owner(session.user_id, principal, session_id)
            await self._command_bus.dispatch(DeleteSessionCommand(session_id=session_id))
        except HTTPException:
            raise
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @staticmethod
    def _require_owner(user_id: str, principal: Principal, session_id: str) -> None:
        if principal.kind == PrincipalKind.SYSTEM or user_id == principal.subject_id:
            return
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
