from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.session.command_handlers.session_handlers.session_not_found import (
    SessionNotFound,
)
from shell.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.domain.platform.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.application.execution.commands.session_commands import CloseSessionCommand
    from shell.application.platform.ports.ports import Clock, UnitOfWork


class SessionCloseHandler:
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, close_session_command: CloseSessionCommand) -> None:
        async with self._unit_of_work as unit_of_work:
            session = await unit_of_work.repository(SessionRepository).get_by_id(SessionId(close_session_command.session_id))
            if session is None:
                raise SessionNotFound(f"Session not found: {close_session_command.session_id}")
            session.close(UpdatedAt.from_datetime(self._clock.now()))
            await unit_of_work.repository(SessionRepository).save(session)
