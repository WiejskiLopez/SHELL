"""AuthSessionCreatedEventHandler — ensures an open Session for a freshly logged-in user.

Consumes ``AuthSessionCreatedIntegrationEvent`` (produced by the User BC when a
user logs in) and guarantees the Session BC holds an open session for that user:

- if the user already has at least one open session → nothing to do (idempotent,
  no duplicate session and no duplicate event);
- otherwise open a new session; the aggregate emits ``SessionOpenedEvent`` which
  the UoW mapper converts to ``SessionOpenedIntegrationEvent`` and stages into the
  Session BC outbox in the same commit as the session change.

Delivery is at-least-once; re-delivery of the same login event is a no-op.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.session.domain.session.aggregates.session import Session
from shell.session.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.session.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.session.domain.session.value_objects.session_status import SessionStatus
from shell.session.domain.session.value_objects.user_id_ref import UserIdRef

if TYPE_CHECKING:
    from shell.platform.application.ports.ports import Clock, IdGenerator
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.session.application.session.session.ports.session_query_service import (
        SessionQueryService,
    )
    from shell.user.application.user.auth_session.integration_events.auth_session_created_integration_event import (
        AuthSessionCreatedIntegrationEvent,
    )


class AuthSessionCreatedEventHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        session_query_service: SessionQueryService,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._session_query_service = session_query_service
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, event: AuthSessionCreatedIntegrationEvent) -> None:
        user_id = event.user_id

        open_sessions, _total = await self._session_query_service.list_all(
            user_id=user_id,
            page_size=1,
        )
        has_open = any(session.status == SessionStatus.OPEN.value for session in open_sessions)
        if has_open:
            return

        await self._open_session(user_id)

    async def _open_session(self, user_id: str) -> None:
        session_id = self._id_generator.new_id(SessionId)
        session = Session.open(
            id_=session_id,
            user_id=UserIdRef(user_id),
            now=CreatedAt.from_datetime(self._clock.now()),
        )
        # save() pulls SessionOpenedEvent and maps it to SessionOpenedIntegrationEvent
        # via the injected mapper; only the integration event reaches the outbox.
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.save(SessionRepository, session)
