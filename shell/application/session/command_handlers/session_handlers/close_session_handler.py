from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.session.command_handlers.session_handlers.session_not_found import (
    SessionNotFound,
)
from shell.domain.execution.value_objects.ids import SessionId
from shell.domain.platform.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.application.platform.commands import CloseSessionCommand
    from shell.application.platform.ports.ports import Clock, UnitOfWork


class CloseSessionHandler:
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, close_session_command: CloseSessionCommand) -> None:
        async with self._unit_of_work as unit_of_work:
            session = await unit_of_work.session_repository.get_by_id(SessionId(close_session_command.session_id))
            if session is None:
                raise SessionNotFound(f"Session not found: {close_session_command.session_id}")
            session.close(UpdatedAt.from_datetime(self._clock.now()))
            await unit_of_work.session_repository.save(session)
