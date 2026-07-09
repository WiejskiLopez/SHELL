"""Unit tests for TaskExecution entity."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_name import (
    TaskExecutionName,
)

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


class TestTaskExecution:
    def test_create_emits_task_created_event(self) -> None:
        task_execution = TaskExecution.create(
            id_=TaskExecutionId.generate(),
            name=TaskExecutionName("my-task"),
            now=_NOW,
        )
        events = task_execution.pull_events()
        assert len(events) == 1
        assert type(events[0]).__name__ == "TaskExecutionCreatedEvent"
