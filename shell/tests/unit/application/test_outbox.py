"""Unit tests — Faza 12 outbox pattern."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.events.events import TaskExecutionCreated, WorkflowStarted
from shell.domain.value_objects.ids import TaskExecutionId, WorkflowId
from shell.domain.value_objects.task_execution_name import TaskExecutionName
from shell.infrastructure.messaging.memory_outbox_store import InMemoryOutboxStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _task_imported() -> TaskExecutionCreated:
    return TaskExecutionCreated.now(
        task_execution_id=TaskExecutionId.generate(),
        task_execution_name=TaskExecutionName("task-name-t1"),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _workflow_started() -> WorkflowStarted:
    return WorkflowStarted.now(
        workflow_id=WorkflowId.generate(),
        task_execution_id=TaskExecutionId("task-id-t1"),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )


# ---------------------------------------------------------------------------
# InMemoryOutboxStore
# ---------------------------------------------------------------------------


class TestInMemoryOutboxStore:
    async def test_publish_adds_records(self) -> None:
        store = InMemoryOutboxStore()
        await store.publish([_task_imported(), _workflow_started()])
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
        assert store.records[0].event_type == "TaskExecutionCreated"

    async def test_empty_publish_no_records(self) -> None:
        store = InMemoryOutboxStore()
        await store.publish([])
        assert store.records == []
