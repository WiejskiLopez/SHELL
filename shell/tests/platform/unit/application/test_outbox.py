"""Unit tests — Faza 12 outbox pattern."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.execution.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.execution.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.context import (
    reset_causation_id,
    reset_correlation_id,
    set_causation_id,
    set_correlation_id,
)
from shell.platform.infrastructure.messaging.memory_outbox_store import InMemoryOutboxStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _task_imported() -> TaskExecutionCreatedEvent:
    return TaskExecutionCreatedEvent.now(
        task_execution_id=TaskExecutionId.generate(),
        now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
    )


# ---------------------------------------------------------------------------
# InMemoryOutboxStore
# ---------------------------------------------------------------------------


class TestInMemoryOutboxStore:
    async def test_publish_adds_records(self) -> None:
        store = InMemoryOutboxStore()
        await store.publish([_task_imported(), _task_imported()])
        assert len(store.records) == 2

    async def test_pending_returns_unpublished(self) -> None:
        store = InMemoryOutboxStore()
        await store.publish([_task_imported(), _task_imported()])
        assert len(store.pending()) == 2

    async def test_marking_published_removes_from_pending(self) -> None:

        store = InMemoryOutboxStore()
        await store.publish([_task_imported()])
        store.records[0].published_at = datetime.now(tz=UTC)
        assert store.pending() == []

    async def test_records_have_event_type(self) -> None:
        store = InMemoryOutboxStore()
        await store.publish([_task_imported()])
        assert store.records[0].event_type == "TaskExecutionCreatedEvent"

    async def test_empty_publish_no_records(self) -> None:
        store = InMemoryOutboxStore()
        await store.publish([])
        assert store.records == []

    async def test_records_have_correlation_id(self) -> None:
        token = set_correlation_id("test-corr-123")
        try:
            store = InMemoryOutboxStore()
            await store.publish([_task_imported()])
            assert store.records[0].correlation_id == "test-corr-123"
        finally:
            reset_correlation_id(token)

    async def test_records_have_causation_id(self) -> None:
        token = set_causation_id("test-caus-456")
        try:
            store = InMemoryOutboxStore()
            await store.publish([_task_imported()])
            assert store.records[0].causation_id == "test-caus-456"
        finally:
            reset_causation_id(token)
