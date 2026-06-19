from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.value_objects.ids import SessionId

from shell.application.execution.command_handlers.session_handlers.session_not_found import SessionNotFound

if TYPE_CHECKING:
    from shell.application.platform.commands.commands import CloseSessionCommand
    from shell.application.platform.ports.ports import Clock, UnitOfWork


class CloseSessionHandler:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def handle(self, cmd: CloseSessionCommand) -> None:
        async with self._uow as uow:
            session = await uow.sessions.get_by_id(SessionId(cmd.session_id))
            if session is None:
                raise SessionNotFound(f"Session not found: {cmd.session_id}")
            session.close(self._clock.now())
            await uow.sessions.save(session)
