from __future__ import annotations

from shell.domain.session.aggregates.session import Session
from shell.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository


class InMemorySessionRepository(InMemoryRepository[Session, SessionId], SessionRepository):
    pass
