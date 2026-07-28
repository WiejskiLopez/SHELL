from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.messaging.aggregates.message_router.message_router import MessageRouter
from shell.domain.messaging.aggregates.message_router.repositories.message_router_repository import (
    MessageRouterRepository,
)
from shell.domain.messaging.aggregates.message_router.value_objects.message_data import MessageData
from shell.domain.messaging.aggregates.message_router.value_objects.message_router_id import (
    MessageRouterId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from shell.application.messaging.message_router.commands.create_message_router_command import (
        CreateMessageRouterCommand,
    )
    from shell.platform.application.ports.identity import IdGenerator
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class CreateMessageRouterHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, command: CreateMessageRouterCommand) -> str:
        now = CreatedAt.from_datetime(self._clock.now())
        message_router_id = self._id_generator.new_id(MessageRouterId)
        message_router = MessageRouter.new(
            id_=message_router_id,
            message_data=MessageData(JsonStr(command.message_data)),
            now=now,
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.save(MessageRouterRepository, message_router)
        return message_router_id.value
