from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.hash import Hash
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.user_service.domain.user.aggregates.auth_session.repositories.auth_session_repository import (
    AuthSessionRepository,
)

if TYPE_CHECKING:
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock
    from shell.user_service.application.user.auth_session.commands.logout_auth_session_command import (
        LogoutAuthSessionCommand,
    )


class LogoutAuthSessionHandler:
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: LogoutAuthSessionCommand) -> None:
        if not command.token:
            return

        async with self._unit_of_work as unit_of_work:
            auth_session = await unit_of_work.repository(AuthSessionRepository).get_by_token_hash(
                Hash.of(command.token)
            )
            if auth_session is None or auth_session.is_deleted:
                return
            if auth_session.revoked_at.value is not None:
                return

            auth_session.revoke(OccurredAt.from_datetime(self._clock.now()))
            await unit_of_work.save(AuthSessionRepository, auth_session)
