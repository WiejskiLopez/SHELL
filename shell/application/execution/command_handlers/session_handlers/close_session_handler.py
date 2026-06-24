from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.execution.command_handlers.session_handlers.session_not_found import (
    SessionNotFound,
)
from shell.domain.execution.value_objects.ids import SessionId

if TYPE_CHECKING:
    from shell.application.platform.commands.commands import CloseSessionCommand
    from shell.application.platform.ports.ports import Clock, UnitOfWork


class CloseSessionHandler:
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: CloseSessionCommand) -> None:
        async with self._unit_of_work as unit_of_work:
            session = await unit_of_work.sessions.get_by_id(SessionId(command.session_id))
            if session is None:
                raise SessionNotFound(f"Session not found: {command.session_id}")
            session.close(self._clock.now())
            await unit_of_work.sessions.save(session)
