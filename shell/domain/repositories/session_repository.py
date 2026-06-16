from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.entities.session import Message, Session
    from shell.domain.value_objects.ids import SessionId


class SessionRepository(Protocol):
    async def save(self, session: Session) -> None: ...
    async def get_by_id(self, session_id: SessionId) -> Session | None: ...
    async def get_messages(self, session_id: SessionId) -> list[Message]: ...
