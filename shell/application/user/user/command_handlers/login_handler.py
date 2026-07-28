from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.user.aggregates.user.events.user_login_succeeded_event import (
    UserLoginSucceededEvent,
)
from shell.domain.user.value_objects.user_id import UserId
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.mapping.reflective_integration_mapper import (
    ReflectiveIntegrationMapper,
)

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
        self._mapper = ReflectiveIntegrationMapper()
        self._queries = queries
        self._clock = clock

    async def handle(self, command: LoginCommand) -> str:
        user = await self._queries.get_by_email(command.email)
        if user is None:
            raise ValueError(f"User with email '{command.email}' not found")

        domain_event = UserLoginSucceededEvent.now(
            user_id=UserId(user.id),
            now=OccurredAt.from_datetime(self._clock.now()),
        )

        integration_event = self._mapper.map(domain_event)

        async with self._unit_of_work as unit_of_work:
            unit_of_work.stage_events([integration_event])

        return user.id
