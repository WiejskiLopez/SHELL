from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.session_service.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.session_service.domain.session.aggregates.session.value_objects.session_id import (
    SessionId,
)

if TYPE_CHECKING:
    from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock
    from shell.session_service.application.session.session.commands.delete_session_command import (
        DeleteSessionCommand,
    )


class SessionNotFoundError(Exception):
    pass


class SessionAlreadyDeletedError(Exception):
    pass


class DeleteSessionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: DeleteSessionCommand) -> None:
        session_id = SessionId(command.session_id)

        async with self._unit_of_work as unit_of_work:
            session = await unit_of_work.repository(SessionRepository).get_by_id(session_id)
            if session is None:
                raise SessionNotFoundError(f"Session '{command.session_id}' not found")

            now = DeletedAt.from_datetime(self._clock.now())
            session.delete(now)
            await unit_of_work.save(SessionRepository, session)
