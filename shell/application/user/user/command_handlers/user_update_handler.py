from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.user.aggregates.user.repositories.user_repository import (
    UserRepository,
)
from shell.domain.user.value_objects.user_email import UserEmail
from shell.domain.user.value_objects.user_id import UserId

if TYPE_CHECKING:
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.application.user.user.commands.update_user_command import UpdateUserCommand
    from shell.domain.platform.ports.time import Clock


class UserNotFoundError(Exception):
    pass


class UserUpdateHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: UpdateUserCommand) -> None:
        user_id = UserId(command.user_id)

        async with self._unit_of_work as unit_of_work:
            user = await unit_of_work.repository(UserRepository).get_by_id(user_id)
            if user is None:
                raise UserNotFoundError(f"User '{command.user_id}' not found")

            now = self._clock.now()
            user.update(email=UserEmail(command.email), now=now)
            await unit_of_work.save(UserRepository, user)
