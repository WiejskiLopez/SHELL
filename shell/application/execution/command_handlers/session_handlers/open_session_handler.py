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
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock, id_generator: IdGenerator) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, open_session_command: OpenSessionCommand) -> SessionId:
        session_id = self._id_generator.new_session_id()
        session = Session.open(
            id_=session_id,
            goal=open_session_command.goal,
            now=self._clock.now(),
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.session_repository.save(session)
        return session_id
