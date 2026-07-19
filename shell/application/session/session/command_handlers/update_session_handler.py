from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.application.session.session.commands.update_session_command import (
        UpdateSessionCommand,
    )
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class SessionNotFoundError(Exception):
    pass


class UpdateSessionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: UpdateSessionCommand) -> None:
        session_id = SessionId(command.session_id)

        async with self._unit_of_work as unit_of_work:
            session = await unit_of_work.repository(SessionRepository).get_by_id(session_id)
            if session is None:
                raise SessionNotFoundError(f"Session '{command.session_id}' not found")

            now = UpdatedAt.from_datetime(self._clock.now())
            session.update(now)
            await unit_of_work.save(SessionRepository, session)
