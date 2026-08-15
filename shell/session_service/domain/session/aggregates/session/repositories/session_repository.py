from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.exists_result import ExistsResult
    from shell.session_service.domain.session.aggregates.session import Session
    from shell.session_service.domain.session.aggregates.session.value_objects.session_id import (
        SessionId,
    )
    from shell.session_service.domain.session.value_objects.user_id_ref import UserIdRef


class SessionRepository(Protocol):
    async def save(self, session: Session) -> None: ...
    async def get_by_id(self, session_id: SessionId) -> Session | None: ...
    async def get_open_by_user_id(self, user_id: UserIdRef) -> Session | None: ...
    async def delete(self, id: SessionId) -> None: ...
    async def exists(self, id: SessionId) -> ExistsResult: ...
