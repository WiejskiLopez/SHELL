from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.domain.session.value_objects.user_id_ref import UserIdRef

if TYPE_CHECKING:
    from shell.application.user.user.integration_events.user_login_succeeded_integration_event import (
        UserLoginSucceededIntegrationEvent,
    )
    from shell.domain.session.services.session_management_service import (
        SessionManagementService,
    )
    from shell.platform.application.ports.ports import Clock, UnitOfWork


class UserLoginSucceededHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        session_service: SessionManagementService,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._session_service = session_service

    async def handle(self, event: UserLoginSucceededIntegrationEvent) -> None:
        user_id_ref = UserIdRef(event.user_id)
        now_dt = self._clock.now()

        async with self._unit_of_work as unit_of_work:
            existing = await unit_of_work.repository(SessionRepository).get_open_by_user_id(
                user_id_ref
            )
            session = self._session_service.ensure_open(
                user_id_ref=user_id_ref,
                now_dt=now_dt,
                existing=existing,
            )
            await unit_of_work.save(SessionRepository, session)
