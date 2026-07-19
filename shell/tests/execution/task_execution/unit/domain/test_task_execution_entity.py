"""Unit tests for TaskExecution entity."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_name import TaskName
from shell.platform.domain.value_objects.created_at import CreatedAt

_NOW = CreatedAt.from_datetime(datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC))


class TestTaskExecution:
    def test_create_emits_task_created_event(self) -> None:
        task_execution = TaskExecution.create(
            id_=TaskExecutionId.generate(),
            name=TaskName("my-task"),
            now=_NOW,
        )
        events = task_execution.pull_events()
        assert len(events) == 1
        assert type(events[0]).__name__ == "TaskExecutionCreatedEvent"

    def test_create_uses_id_as_default_name(self) -> None:
        id_ = TaskExecutionId.generate()
        task_execution = TaskExecution.create(
            id_=id_,
            now=_NOW,
        )
        assert task_execution.name.value == str(id_.value)
