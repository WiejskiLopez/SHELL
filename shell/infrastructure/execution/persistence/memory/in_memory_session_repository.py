from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session.ports.session_repository import SessionRepository
from shell.domain.execution.value_objects.ids import (
    SessionId,  # noqa: TC002 — SessionId używany w konstruktorach w repozytorium
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session import Session


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._store: dict[str, Session] = {}

    async def save(self, session: Session) -> None:
        self._store[session.id.value] = session

    async def get_by_id(self, session_id: SessionId) -> Session | None:
        return self._store.get(session_id.value)
