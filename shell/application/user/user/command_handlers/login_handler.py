from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.user.aggregates.user.repositories.user_repository import UserRepository
from shell.domain.user.value_objects.user_id import UserId
from shell.platform.domain.value_objects.occurred_at import OccurredAt

if TYPE_CHECKING:
    from shell.application.user.user.commands.login_command import LoginCommand
    from shell.application.user.user.ports.user_query_service import UserQueryService
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class LoginHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        queries: UserQueryService,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._queries = queries
        self._clock = clock

    async def handle(self, command: LoginCommand) -> str:
        async with self._unit_of_work as unit_of_work:
            user_dto = await self._queries.get_by_email(command.email)
            if user_dto is None:
                raise ValueError(f"User with email '{command.email}' not found")

            user = await unit_of_work.repository(UserRepository).get_by_id(UserId(user_dto.id))
            if user is None:
                raise ValueError(f"User with id '{user_dto.id}' not found")

            user.login(OccurredAt.from_datetime(self._clock.now()))
            await unit_of_work.save(UserRepository, user)

        return user.id.value
