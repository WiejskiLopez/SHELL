from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.application.command_handlers.command_handler import CommandHandler
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.user_service.application.user.user.commands.change_user_command import (
    ChangeUserCommand,
)
from shell.user_service.domain.user.aggregates.user.repositories.user_repository import (
    UserRepository,
)
from shell.user_service.domain.user.value_objects.user_email import UserEmail
from shell.user_service.domain.user.value_objects.user_id import UserId

if TYPE_CHECKING:
    from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


from shell.user_service.application.user.user.exceptions.user_not_found_error import (
    UserNotFoundError,
)


class ChangeUserHandler(CommandHandler[ChangeUserCommand]):
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: ChangeUserCommand) -> None:
        user_id = UserId(command.user_id)

        async with self._unit_of_work as unit_of_work:
            user = await unit_of_work.repository(UserRepository).get_by_id(user_id)
            if user is None:
                raise UserNotFoundError(f"User '{command.user_id}' not found")

            now = OccurredAt.from_datetime(self._clock.now())
            user.change(email=UserEmail(command.email), now=now)
            await unit_of_work.save(UserRepository, user)
