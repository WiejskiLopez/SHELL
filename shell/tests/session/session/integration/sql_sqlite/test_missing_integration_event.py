"""SQLite integration tests — missing integration event must fail, not drop silently."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.infrastructure.mapping.integration_mapping_error import (
    IntegrationMappingError,
)
from shell.platform.infrastructure.mapping.reflective_integration_mapper import (
    ReflectiveIntegrationMapper,
)
from shell.session.domain.session.aggregates.session import Session
from shell.session.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.session.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.session.domain.session.value_objects.user_id_ref import UserIdRef
from shell.session.infrastructure.session.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.session.infrastructure.session.session.persistence.sql.unit_of_work import (
    SqlAlchemySessionUnitOfWork,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class _UnmappedDomainEvent:
    """A domain event that has no ``*IntegrationEvent`` counterpart."""

    __module__ = "shell.session.domain.session.aggregates.session.events.no_such_event"
    __name__ = "NoSuchEvent"
    event_id = type("id", (), {"value": "x"})()
    occurred_at = type("oa", (), {"value": datetime(2025, 1, 1, tzinfo=UTC)})()
    aggregate_id = type("id", (), {"value": ""})()
    aggregate_name = type("n", (), {"value": ""})()
    schema_version = type("v", (), {"value": 1})()


class TestMissingIntegrationEvent:
    async def test_mapper_raises_for_unmapped_domain_event(self) -> None:
        with pytest.raises(IntegrationMappingError, match="Cannot find integration event"):
            ReflectiveIntegrationMapper().map(_UnmappedDomainEvent())

    async def test_uow_save_with_mapper_does_not_write_outbox_when_mapping_fails(
        self,
        session_factory: async_sessionmaker,
        sql_uow: SqlAlchemySessionUnitOfWork,
    ) -> None:
        mapper = ReflectiveIntegrationMapper()
        uow = SqlAlchemySessionUnitOfWork(
            session_factory, mapper=mapper, models=PERSISTENCE_DELIVERY_MODELS
        )

        session = Session.open(
            id_=SessionId("unmapped-session"),
            user_id=UserIdRef("user-x"),
            now=CreatedAt.from_datetime(datetime(2025, 1, 1, tzinfo=UTC)),
        )
        # Append a domain event that has no integration contract to simulate a
        # missing mapping.
        session.append_event(_UnmappedDomainEvent())  # type: ignore[arg-type]

        with pytest.raises(IntegrationMappingError):
            async with uow as unit_of_work:
                await unit_of_work.save(SessionRepository, session)

        async with session_factory() as connection:
            outbox_rows = (
                (await connection.execute(select(PERSISTENCE_DELIVERY_MODELS.events.outbox)))
                .scalars()
                .all()
            )
        assert outbox_rows == []

    async def test_uow_save_with_mapper_does_not_persist_aggregate_when_mapping_fails(
        self,
        session_factory: async_sessionmaker,
        sql_uow: SqlAlchemySessionUnitOfWork,
    ) -> None:
        mapper = ReflectiveIntegrationMapper()
        uow = SqlAlchemySessionUnitOfWork(
            session_factory, mapper=mapper, models=PERSISTENCE_DELIVERY_MODELS
        )

        session = Session.open(
            id_=SessionId("unmapped-session-2"),
            user_id=UserIdRef("user-x"),
            now=CreatedAt.from_datetime(datetime(2025, 1, 1, tzinfo=UTC)),
        )
        session.append_event(_UnmappedDomainEvent())  # type: ignore[arg-type]

        with pytest.raises(IntegrationMappingError):
            async with uow as unit_of_work:
                await unit_of_work.save(SessionRepository, session)

        from shell.session.infrastructure.session.session.persistence.sql.models.session import (
            SessionModel,
        )

        async with session_factory() as connection:
            rows = (await connection.execute(select(SessionModel))).scalars().all()
        assert rows == []
