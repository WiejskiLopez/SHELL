"""Unit tests for AuthSessionCreatedEventHandler (opens/ensures a Session)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.session.application.session.session.event_handlers.auth_session_created_event_handler import (
    AuthSessionCreatedEventHandler,
)
from shell.session.application.session.session.integration_events.session_opened_integration_event import (
    SessionOpenedIntegrationEvent,
)
from shell.session.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.user.application.user.auth_session.integration_events.auth_session_created_integration_event import (
    AuthSessionCreatedIntegrationEvent,
)

if TYPE_CHECKING:
    from shell.platform.infrastructure.persistence.memory import FakeClock, FakeIdGenerator
    from shell.session.infrastructure.session.persistence.memory.query_services import (
        InMemorySessionQueryService,
    )
    from shell.session.infrastructure.session.persistence.memory.unit_of_work import (
        InMemorySessionUnitOfWork,
    )


def _login_event(user_id: str = "user-1") -> AuthSessionCreatedIntegrationEvent:
    return AuthSessionCreatedIntegrationEvent(
        event_id="event-login-1",
        correlation_id="corr-1",
        causation_id="cause-0",
        occurred_at=datetime(2024, 1, 1, tzinfo=UTC),
        aggregate_id="auth-session-1",
        aggregate_name="AuthSession",
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
        handler = AuthSessionCreatedEventHandler(unit_of_work, queries, clock, id_generator)
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
        unit_of_work: InMemorySessionUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        queries: InMemorySessionQueryService,
    ) -> None:
        # Pre-open a session for user-1 via the domain aggregate.
        from shell.platform.domain.value_objects.created_at import CreatedAt
        from shell.session.domain.session.aggregates.session import Session
        from shell.session.domain.session.aggregates.session.value_objects.session_id import (
            SessionId,
        )
        from shell.session.domain.session.value_objects.user_id_ref import UserIdRef

        session = Session.open(
            id_=SessionId("session-existing"),
            user_id=UserIdRef("user-1"),
            now=CreatedAt.from_datetime(datetime(2024, 1, 1, tzinfo=UTC)),
        )
        async with unit_of_work as uow:
            await uow.save(SessionRepository, session)

        # Fresh UoW for the handler, so committed_events reflects only the handler.
        from shell.session.infrastructure.session.persistence.memory.unit_of_work import (
            InMemorySessionUnitOfWork,
        )

        handler_uow = InMemorySessionUnitOfWork()
        handler = AuthSessionCreatedEventHandler(
            handler_uow,
            queries,
            clock,
            id_generator,
        )
        await handler.handle(_login_event())

        open_sessions, total = await queries.list_all(user_id="user-1")
        assert total == 1
        assert open_sessions[0].id == "session-existing"

        # Idempotent: existing open session → no duplicate event emitted.
        assert handler_uow.committed_events == []
