from __future__ import annotations

from typing import TYPE_CHECKING

from shell.session_service.application.session.session.dto.session import SessionDto
from shell.session_service.domain.session.aggregates.session.value_objects.session_id import (
    SessionId,
)
from shell.session_service.infrastructure.session.session.persistence.memory.in_memory_session_repository import (
    InMemorySessionRepository,
)

if TYPE_CHECKING:
    from shell.session_service.infrastructure.session.persistence.memory.unit_of_work import (
        InMemorySessionUnitOfWork,
    )


class InMemorySessionQueryService:
    def __init__(self, unit_of_work: InMemorySessionUnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    async def get_by_id(self, session_id: str) -> SessionDto | None:
        session = await self._unit_of_work.repository(InMemorySessionRepository).get_by_id(
            SessionId(session_id)
        )
        if session is None:
            return None
        return SessionDto(
            id=session.id.value,
            user_id=session.user_id.value,
            status=session._status,
            opened_at=session.opened_at.value,
            closed_at=session.closed_at.value if session.closed_at else None,
            created_at=session.created_at.value,
        )

    async def list_all(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
        user_id: str | None = None,
    ) -> tuple[list[SessionDto], int]:
        repository = self._unit_of_work.repository(InMemorySessionRepository)
        sessions = [session for session in repository.all()]
        if user_id is not None:
            sessions = [s for s in sessions if s.user_id.value == user_id]
        dtos = [
            SessionDto(
                id=session.id.value,
                user_id=session.user_id.value,
                status=session.session_status.value,
                opened_at=session.opened_at.value,
                closed_at=session.closed_at.value if session.closed_at else None,
                created_at=session.created_at.value,
                changed_at=session.changed_at.value if session.changed_at else None,
                deleted_at=session.deleted_at.value if session.deleted_at else None,
            )
            for session in sessions
        ]
        return dtos, len(dtos)
