from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session import Session
from shell.domain.execution.value_objects.ids import (
    SessionId,  # noqa: TC002 — SessionId używany jako typ zwracany handle() i w konstruktorach
)

if TYPE_CHECKING:
    from shell.application.platform.commands.commands import OpenSessionCommand
    from shell.application.platform.ports.ports import Clock, IdGenerator, UnitOfWork


class OpenSessionHandler:
    def __init__(self, uow: UnitOfWork, clock: Clock, id_gen: IdGenerator) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen

    async def handle(self, cmd: OpenSessionCommand) -> SessionId:
        session_id = self._id_gen.new_session_id()
        session = Session.open(
            id_=session_id,
            goal=cmd.goal,
            now=self._clock.now(),
        )
        async with self._uow as uow:
            await uow.sessions.save(session)
        return session_id
