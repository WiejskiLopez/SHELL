from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.messaging.aggregates.message_router.repositories.message_router_repository import (
    MessageRouterRepository,
)
from shell.domain.messaging.aggregates.message_router.value_objects.message_router_id import (
    MessageRouterId,
)
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.application.messaging.message_router.commands.update_message_router_command import (
        UpdateMessageRouterCommand,
    )
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class MessageRouterNotFoundError(Exception):
    pass


class UpdateMessageRouterHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: UpdateMessageRouterCommand) -> None:
        message_router_id = MessageRouterId(command.message_router_id)
        async with self._unit_of_work as unit_of_work:
            message_router = await unit_of_work.repository(MessageRouterRepository).get_by_id(
                message_router_id
            )
            if message_router is None:
                raise MessageRouterNotFoundError(
                    f"MessageRouter '{command.message_router_id}' not found"
                )
            now = UpdatedAt.from_datetime(self._clock.now())
            message_router.update(now)
            await unit_of_work.save(MessageRouterRepository, message_router)
