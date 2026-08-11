from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository
from shell.session.domain.session.aggregates.session import Session
from shell.session.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.session.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.session.domain.session.value_objects.session_status import SessionStatus

if TYPE_CHECKING:
    from shell.session.domain.session.value_objects.user_id_ref import UserIdRef


class InMemorySessionRepository(InMemoryRepository[Session, SessionId], SessionRepository):
    async def get_open_by_user_id(self, user_id: UserIdRef) -> Session | None:
        for session in self._store.values():
            if (
                session.user_id == user_id
                and session.session_status == SessionStatus.OPEN
                and session.deleted_at.value is None
            ):
                return session
        return None
