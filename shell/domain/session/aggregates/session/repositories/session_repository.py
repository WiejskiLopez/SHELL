from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.value_objects.exists_result import ExistsResult
    from shell.domain.session.aggregates.session import Session
    from shell.domain.session.aggregates.session.value_objects.session_id import SessionId


class SessionRepository(Protocol):
    async def save(self, session: Session) -> None: ...
    async def get_by_id(self, session_id: SessionId) -> Session | None: ...
    async def delete(self, id: SessionId) -> None: ...
    async def exists(self, id: SessionId) -> ExistsResult: ...
