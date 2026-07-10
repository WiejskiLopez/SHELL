from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.user.aggregates.user.repositories.user_repository import (
    UserRepository,
)
from shell.domain.user.value_objects.user_id import UserId

if TYPE_CHECKING:
    from shell.application.user.user.commands.delete_user_command import DeleteUserCommand
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class UserNotFoundError(Exception):
    pass


class UserAlreadyDeletedError(Exception):
    pass


class DeleteUserHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: DeleteUserCommand) -> None:
        user_id = UserId(command.user_id)

        async with self._unit_of_work as unit_of_work:
            user = await unit_of_work.repository(UserRepository).get_by_id(user_id)
            if user is None:
                raise UserNotFoundError(f"User '{command.user_id}' not found")

            if user.is_deleted:
                raise UserAlreadyDeletedError(f"User '{command.user_id}' is already deleted")

            now = self._clock.now()
            user.delete(now)
            await unit_of_work.save(UserRepository, user)
