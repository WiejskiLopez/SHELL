"""Unit tests for AuthSessionCreatedEventHandler (opens/ensures a Session)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.session_service.application.session.session.event_handlers.auth_session_created_event_handler import (
    AuthSessionCreatedEventHandler,
)
from shell.session_service.application.session.session.integration_events.auth_session_created_integration_event import (
    AuthSessionCreatedIntegrationEvent,
)
from shell.session_service.application.session.session.integration_events.session_opened_integration_event import (
    SessionOpenedIntegrationEvent,
)
from shell.session_service.infrastructure.session.session.persistence.memory.in_memory_session_repository import (
    InMemorySessionRepository,
)

if TYPE_CHECKING:
    from shell.platform.infrastructure.persistence.memory import FakeClock, FakeIdGenerator
    from shell.session_service.infrastructure.session.persistence.memory.query_services import (
        InMemorySessionQueryService,
    )
    from shell.session_service.infrastructure.session.persistence.memory.unit_of_work import (
        InMemorySessionUnitOfWork,
    )


def _login_event(user_id: str = "user-1") -> AuthSessionCreatedIntegrationEvent:
    return AuthSessionCreatedIntegrationEvent(
        event_id="event-login-1",
        correlation_id="corr-1",
        causation_id="cause-0",
        occurred_at=datetime(2024, 1, 1, tzinfo=UTC),
        aggregate_id="auth-session-1",
        schema_version=1,
        auth_session_id="auth-session-1",
        user_id=user_id,
    )


class TestAuthSessionCreatedEventHandler:
    async def test_opens_session_when_user_has_none(
        self,
        unit_of_work: InMemorySessionUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        queries: InMemorySessionQueryService,
    ) -> None:
        handler = AuthSessionCreatedEventHandler(unit_of_work, clock, id_generator)
        await handler.handle(_login_event())

        open_sessions, total = await queries.list_all(user_id="user-1")
        assert total == 1
        assert open_sessions[0].status == "OPEN"

        assert any(
            isinstance(event, SessionOpenedIntegrationEvent) and event.user_id == "user-1"
            for event in unit_of_work.committed_events
        )

    async def test_reuses_existing_open_session(
        self,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        # Pre-open a session for user-1 in the same UoW the handler will use,
        # mirroring a DB that already holds an open session.
        from shell.platform.domain.value_objects.created_at import CreatedAt
        from shell.session_service.domain.session.aggregates.session import Session
        from shell.session_service.domain.session.aggregates.session.value_objects.session_id import (
            SessionId,
        )
        from shell.session_service.domain.session.value_objects.user_id_ref import UserIdRef
        from shell.session_service.infrastructure.session.persistence.memory.unit_of_work import (
            InMemorySessionUnitOfWork,
        )

        session = Session.open(
            id_=SessionId("session-existing"),
            user_id=UserIdRef("user-1"),
            now=CreatedAt.from_datetime(datetime(2024, 1, 1, tzinfo=UTC)),
        )
        handler_uow = InMemorySessionUnitOfWork()
        await handler_uow.repository(InMemorySessionRepository).save(session)

        handler = AuthSessionCreatedEventHandler(handler_uow, clock, id_generator)
        await handler.handle(_login_event())

        existing = await handler_uow.repository(InMemorySessionRepository).get_open_by_user_id(
            UserIdRef("user-1")
        )
        assert existing is not None
        assert existing.id.value == "session-existing"

        # Idempotent: existing open session → no duplicate event emitted.
        assert handler_uow.committed_events == []
