"""Faza 3 tests — SQL readiness probe (ref2.md §5 Faza 3, ref4.md Krok 4)."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from shell.execution_service.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.mapping.reflective_integration_mapper import (
    ReflectiveIntegrationMapper,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.serialization.integration_event.integration_event_serializer import (
    IntegrationEventSerializer,
)
from shell.platform.observability.infrastructure.health.rabbit_readiness_probe import (
    RabbitReadinessProbe,
)
from shell.platform.observability.infrastructure.health.sql_readiness_probe import SqlReadinessProbe
from shell.tests.platform.integration.platform_delivery_models import (
    EVENT_DELIVERY_MODELS,
    PERSISTENCE_DELIVERY_MODELS,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.execution_service.application.execution.task_execution.integration_events.task_execution_created_integration_event import (
        TaskExecutionCreatedIntegrationEvent,
    )

_INBOX_MODEL: Any = EVENT_DELIVERY_MODELS.inbox
_WORKER_HEARTBEAT_MODEL: Any = PERSISTENCE_DELIVERY_MODELS.worker_heartbeat

RABBIT_TEST_URL = os.environ.get("RABBIT_TEST_URL")
_rabbit_available = RABBIT_TEST_URL is not None

skip_no_rabbit = pytest.mark.skipif(
    not _rabbit_available,
    reason="RABBIT_TEST_URL not set — start shell/rabbitmq/docker/docker-compose.yml to enable",
)


def _event() -> TaskExecutionCreatedIntegrationEvent:
    domain_event = TaskExecutionCreatedEvent.now(
        task_execution_id=TaskExecutionId.generate(),
        now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
    )
    return cast(
        "TaskExecutionCreatedIntegrationEvent",
        ReflectiveIntegrationMapper().map(domain_event),
    )


async def _seed_pending(session_factory: async_sessionmaker, count: int) -> None:
    serializer = IntegrationEventSerializer()
    async with session_factory() as session:
        for index in range(count):
            event = _event()
            session.add(
                _INBOX_MODEL(
                    id=f"evt-ready-{index}",
                    event_id=event.event_id,
                    source_service="execution_service",
                    integration_event_name=type(event).__name__,
                    occurred_at=event.occurred_at,
                    aggregate_id=event.aggregate_id,
                    payload=serializer.to_payload(event),
                    correlation_id="corr",
                    causation_id="cause",
                    received_at=datetime.now(tz=UTC),
                    status=InboxStatus.PENDING.value,
                )
            )
        await session.commit()


class TestSqlReadinessProbe:
    async def test_ready_when_database_up_and_no_backlog(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        probe = SqlReadinessProbe(
            session_factory,
            _INBOX_MODEL,
            max_backlog=10,
        )
        report = await probe.check()

        assert report.ready is True
        assert report.checks["database"] is True
        assert report.checks["migrations"] is True
        assert report.checks["worker"] is True
        assert report.checks["backlog"] is True

    async def test_backlog_over_threshold_is_not_ready(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _seed_pending(session_factory, 5)
        probe = SqlReadinessProbe(
            session_factory,
            _INBOX_MODEL,
            max_backlog=3,
        )
        report = await probe.check()

        assert report.ready is False
        assert report.checks["backlog"] is False

    async def test_database_down_is_not_ready(self) -> None:
        broken_factory = build_session_factory("sqlite+aiosqlite:///./missing-{uuid}.db")
        probe = SqlReadinessProbe(
            broken_factory,
            _INBOX_MODEL,
            max_backlog=10,
        )
        report = await probe.check()

        assert report.ready is False
        assert report.checks["database"] is not True


class TestWorkerHeartbeatReadiness:
    async def _isolated(
        self,
        tmp_path,
    ) -> async_sessionmaker:
        url = f"sqlite+aiosqlite:///{tmp_path / 'readiness-hb.db'}"
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.run_sync(EVENT_DELIVERY_MODELS.inbox.metadata.create_all)
            await connection.run_sync(_WORKER_HEARTBEAT_MODEL.metadata.create_all)
        await engine.dispose()
        return build_session_factory(url)

    async def _seed_pending(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        serializer = IntegrationEventSerializer()
        event = _event()
        async with session_factory() as session:
            session.add(
                _INBOX_MODEL(
                    id="evt-hb-pending",
                    event_id=event.event_id,
                    source_service="execution_service",
                    integration_event_name=type(event).__name__,
                    occurred_at=datetime.now(tz=UTC),
                    aggregate_id=event.aggregate_id,
                    payload=serializer.to_payload(event),
                    correlation_id="corr",
                    causation_id="cause",
                    received_at=datetime.now(tz=UTC),
                    status=InboxStatus.PENDING.value,
                )
            )
            await session.commit()

    async def test_fresh_worker_heartbeat_means_ready(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        isolated = await self._isolated(tmp_path)
        async with isolated() as session:
            session.add(
                _WORKER_HEARTBEAT_MODEL(
                    worker_id="worker-a",
                    last_seen_at=datetime.now(tz=UTC),
                )
            )
            await session.commit()

        probe = SqlReadinessProbe(
            isolated,
            _INBOX_MODEL,
            max_backlog=10,
            worker_heartbeat_model=_WORKER_HEARTBEAT_MODEL,
            worker_stale_after_seconds=30,
        )
        report = await probe.check()
        assert report.ready is True
        assert report.checks["worker"] is True

    async def test_stale_worker_with_backlog_is_not_ready(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        isolated = await self._isolated(tmp_path)
        await self._seed_pending(isolated)
        async with isolated() as session:
            session.add(
                _WORKER_HEARTBEAT_MODEL(
                    worker_id="worker-a",
                    last_seen_at=datetime.now(tz=UTC) - timedelta(minutes=10),
                )
            )
            await session.commit()

        probe = SqlReadinessProbe(
            isolated,
            _INBOX_MODEL,
            max_backlog=10,
            worker_heartbeat_model=_WORKER_HEARTBEAT_MODEL,
            worker_stale_after_seconds=30,
        )
        report = await probe.check()
        assert report.ready is False
        assert report.checks["worker"] is False

    async def test_no_worker_and_no_backlog_is_not_ready(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        isolated = await self._isolated(tmp_path)
        probe = SqlReadinessProbe(
            isolated,
            _INBOX_MODEL,
            max_backlog=10,
            worker_heartbeat_model=_WORKER_HEARTBEAT_MODEL,
            worker_stale_after_seconds=30,
        )
        report = await probe.check()
        assert report.ready is False
        assert report.checks["worker"] is False


class TestRabbitReadinessProbeIntegration:
    @skip_no_rabbit
    async def test_ready_when_broker_reachable(self) -> None:
        probe = RabbitReadinessProbe(url_provider=lambda: RABBIT_TEST_URL or "")
        report = await probe.check()

        assert report.ready is True
        assert report.checks["broker"] is True

    async def test_not_ready_when_broker_unreachable(self) -> None:
        probe = RabbitReadinessProbe(
            url_provider=lambda: "amqp://127.0.0.1:1",
            timeout=0.5,
        )
        report = await probe.check()

        assert report.ready is False
        broker_check = report.checks["broker"]
        assert isinstance(broker_check, str)
        assert "error:" in broker_check

    async def test_not_ready_when_broker_url_missing(self) -> None:
        probe = RabbitReadinessProbe(url_provider=lambda: "")
        report = await probe.check()

        assert report.ready is False
        assert report.checks["broker"] == "error: broker URL is not configured"
