"""SQLite integration tests — message outbox atomicity in ``SqlAlchemyUnitOfWorkBase``.

An aggregate-sourced message is a side effect of a domain mutation: the outbox
row must land in the same transaction as the aggregate change (commit) and must
never survive a handler failure (rollback). These tests verify the
``stage_messages`` → ``outbox_message`` write path.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy import select

from shell.ingestion_service.domain.ingestion.aggregates.ingestion.payloads.ingestion_payload import (
    IngestionPayload,
)
from shell.ingestion_service.domain.ingestion.aggregates.ingestion.value_objects.ingestion_data import (
    IngestionData,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.aggregate_id import AggregateId
from shell.platform.domain.value_objects.aggregate_name import AggregateName
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.infrastructure.context import (
    reset_causation_id,
    reset_correlation_id,
    set_causation_id,
    set_correlation_id,
)
from shell.platform.infrastructure.mapping.reflective_integration_mapper import (
    ReflectiveIntegrationMapper,
)
from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)
from shell.platform.types import JsonStr
from shell.tests.platform.integration.platform_delivery_models import PERSISTENCE_DELIVERY_MODELS

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.platform.domain.messages import DomainMessage

_MESSAGE_OUTBOX = PERSISTENCE_DELIVERY_MODELS.messages.outbox


def _ingestion_payload() -> IngestionPayload:
    return IngestionPayload(
        occurred_at=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
        ingestion_data=IngestionData(JsonStr(json.dumps({"type": "test"}))),
        recipient_aggregate_id=AggregateId("agent-1"),
        recipient_aggregate_name=AggregateName("Agent"),
        state_data=StateData(JsonStr.from_object({"type": "test"})),
    )


async def _outbox_message_rows(session_factory: async_sessionmaker) -> list[Any]:
    async with session_factory() as session:
        rows = (await session.execute(select(_MESSAGE_OUTBOX))).scalars().all()
        return list(rows)


class TestMessageOutboxAtomicity:
    async def test_commit_writes_message_outbox_row(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        baseline = len(await _outbox_message_rows(session_factory))
        uow = SqlAlchemyUnitOfWorkBase(
            session_factory,
            mapper=ReflectiveIntegrationMapper(),
            models=PERSISTENCE_DELIVERY_MODELS,
        )
        async with uow:
            uow.stage_messages([_ingestion_payload()])

        rows = await _outbox_message_rows(session_factory)
        assert len(rows) == baseline + 1
        assert rows[-1].message_type == "IngestionPayload"
        assert rows[-1].payload

    async def test_handler_failure_writes_no_message_outbox_row(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        baseline = len(await _outbox_message_rows(session_factory))
        uow = SqlAlchemyUnitOfWorkBase(
            session_factory,
            mapper=ReflectiveIntegrationMapper(),
            models=PERSISTENCE_DELIVERY_MODELS,
        )
        with pytest.raises(RuntimeError, match="boom"):
            async with uow:
                uow.stage_messages([_ingestion_payload()])
                raise RuntimeError("boom")

        assert len(await _outbox_message_rows(session_factory)) == baseline


class _MessageAggregate(AggregateRoot[int]):
    def __init__(self) -> None:
        super().__init__(1)

    def emit(self, message: DomainMessage) -> None:
        self.append_message(message)


class _FakeRepository:
    def __init__(self, session: Any) -> None:
        self._session = session
        self.saved: list[object] = []

    async def save(self, aggregate: object) -> None:
        self.saved.append(aggregate)


class _MessageOutboxUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def _build_repo_map(self) -> dict[type, type]:
        return {_FakeRepository: _FakeRepository}


class TestAggregateSourcedMessageOutbox:
    async def test_save_pulls_and_persists_messages_atomically(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        correlation_token = set_correlation_id("corr-content-1")
        causation_token = set_causation_id("cause-content-1")
        try:
            aggregate = _MessageAggregate()
            aggregate.emit(_ingestion_payload())

            baseline = len(await _outbox_message_rows(session_factory))
            uow = _MessageOutboxUnitOfWork(
                session_factory,
                mapper=ReflectiveIntegrationMapper(),
                models=PERSISTENCE_DELIVERY_MODELS,
            )
            async with uow:
                await uow.save(_FakeRepository, aggregate)

            rows = await _outbox_message_rows(session_factory)
            assert len(rows) == baseline + 1
            assert rows[-1].message_type == "IngestionPayload"
            assert rows[-1].correlation_id == "corr-content-1"
            assert rows[-1].causation_id == "cause-content-1"
            assert rows[-1].payload["ingestion_data"] == '{"type": "test"}'
        finally:
            reset_correlation_id(correlation_token)
            reset_causation_id(causation_token)

    async def test_save_on_failure_persists_no_message_row(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        aggregate = _MessageAggregate()
        aggregate.emit(_ingestion_payload())

        baseline = len(await _outbox_message_rows(session_factory))
        uow = _MessageOutboxUnitOfWork(
            session_factory,
            mapper=ReflectiveIntegrationMapper(),
            models=PERSISTENCE_DELIVERY_MODELS,
        )
        with pytest.raises(RuntimeError, match="boom"):
            async with uow:
                await uow.save(_FakeRepository, aggregate)
                raise RuntimeError("boom")

        assert len(await _outbox_message_rows(session_factory)) == baseline
