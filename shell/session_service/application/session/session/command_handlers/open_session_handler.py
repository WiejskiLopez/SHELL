from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.session_service.domain.session.aggregates.session import Session
from shell.session_service.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.session_service.domain.session.aggregates.session.value_objects.session_id import (
    SessionId,
)
from shell.session_service.domain.session.value_objects.user_id_ref import UserIdRef

if TYPE_CHECKING:
    from shell.platform.application.ports.ports import Clock, IdGenerator, UnitOfWork
    from shell.session_service.application.session.session.commands.open_session_command import (
        OpenSessionCommand,
    )


class OpenSessionHandler:
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock, id_generator: IdGenerator) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, command: OpenSessionCommand) -> SessionId:
        session_id = self._id_generator.new_id(SessionId)
        session = Session.open(
            id_=session_id,
            user_id=UserIdRef(command.user_id),
            goal=command.goal,
            now=CreatedAt.from_datetime(self._clock.now()),
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.save(SessionRepository, session)
        return session_id
