from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.updated_at import UpdatedAt
from shell.session.application.session.session.exceptions.session_not_found import (
    SessionNotFound,
)
from shell.session.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.session.domain.session.aggregates.session.value_objects.session_id import SessionId

if TYPE_CHECKING:
    from shell.platform.application.ports.ports import Clock, UnitOfWork
    from shell.session.application.session.session.commands.close_session_command import (
        CloseSessionCommand,
    )


class CloseSessionHandler:
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: CloseSessionCommand) -> None:
        async with self._unit_of_work as unit_of_work:
            session = await unit_of_work.repository(SessionRepository).get_by_id(
                SessionId(command.session_id)
            )
            if session is None:
                raise SessionNotFound(f"Session not found: {command.session_id}")
            session.close(UpdatedAt.from_datetime(self._clock.now()))
            await unit_of_work.save(SessionRepository, session)
