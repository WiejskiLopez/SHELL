from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.repositories.session_repository import SessionRepository
from shell.domain.value_objects.ids import SessionId

if TYPE_CHECKING:
    from shell.domain.entities.session import Message, Session


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._store: dict[str, Session] = {}
        self._messages: dict[str, list[Message]] = {}

    async def save(self, session: Session) -> None:
        self._store[session.id.value] = session
        existing = self._messages.get(session.id.value, [])
        existing_ids = {message.id.value for message in existing}
        for msg in session.messages:
            if msg.id.value not in existing_ids:
                existing.append(msg)
        self._messages[session.id.value] = existing

    async def get_by_id(self, session_id: SessionId) -> Session | None:
        return self._store.get(session_id.value)

    async def get_messages(self, session_id: SessionId) -> list[Message]:
        return list(self._messages.get(session_id.value, []))
