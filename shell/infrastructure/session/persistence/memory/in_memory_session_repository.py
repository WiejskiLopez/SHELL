from __future__ import annotations

from shell.domain.execution.value_objects.ids import (
    SessionId,
)
from shell.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.domain.session.aggregates.session import Session
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository


class InMemorySessionRepository(InMemoryRepository[Session, SessionId], SessionRepository):
    pass
