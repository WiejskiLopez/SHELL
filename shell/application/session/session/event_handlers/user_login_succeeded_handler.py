from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.session.aggregates.session import Session
from shell.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.domain.session.value_objects.user_id_ref import UserIdRef
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.application.user.user.integration_events.user_login_succeeded_integration_event import (
        UserLoginSucceededIntegrationEvent,
    )
    from shell.platform.application.ports.ports import Clock, IdGenerator, UnitOfWork


class UserLoginSucceededHandler:
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock, id_generator: IdGenerator) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, event: UserLoginSucceededIntegrationEvent) -> None:
        user_id_ref = UserIdRef(event.user_id)
        now = CreatedAt.from_datetime(self._clock.now())

        async with self._unit_of_work as unit_of_work:
            existing = await unit_of_work.repository(SessionRepository).get_open_by_user_id(
                user_id_ref
            )

            if existing is not None:
                existing.update(UpdatedAt.from_datetime(now.value))
                await unit_of_work.save(SessionRepository, existing)
            else:
                session_id = self._id_generator.new_id(SessionId)
                session = Session.open(id_=session_id, user_id=user_id_ref, now=now)
                await unit_of_work.save(SessionRepository, session)
