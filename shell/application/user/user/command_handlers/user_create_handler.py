from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.user.aggregates.user.repositories.user_repository import (
    UserRepository,
)
from shell.domain.user.aggregates.user.user import User
from shell.domain.user.value_objects.user_email import UserEmail
from shell.domain.user.value_objects.user_id import UserId

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.application.user.user.commands.create_user_command import CreateUserCommand
    from shell.domain.platform.ports.time import Clock


class UserCreateHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, command: CreateUserCommand) -> str:
        now = self._clock.now()
        user_id = self._id_generator.new_id(UserId)

        user = User(
            id=user_id,
            email=UserEmail(command.email),
            created_at=CreatedAt.from_datetime(now),
        )

        async with self._unit_of_work as unit_of_work:
            await unit_of_work.repository(UserRepository).save(user)
            unit_of_work.stage_events(user.pull_events())

        return user_id.value
