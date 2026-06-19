"""Unit tests for TaskExecution entity."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.aggregates.task_execution import TaskExecution
from shell.domain.value_objects.ids import TaskExecutionId
from shell.domain.value_objects.task_execution_body import TaskExecutionBody
from shell.domain.value_objects.task_execution_name import TaskExecutionName
from shell.domain.value_objects.version import Version

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


class TestTaskExecution:
    def test_create_yields_initial_task(self) -> None:
        task_execution = TaskExecution.create(
            id_=TaskExecutionId.generate(),
            name=TaskExecutionName("task-name"),
            body=TaskExecutionBody("task-body"),
            now=_NOW,
        )
        assert task_execution.is_current is True
        assert task_execution.version == Version.initial()
        assert len(task_execution.hash.value) == 64

    def test_create_emits_task_created_event(self) -> None:
        task_execution = TaskExecution.create(
            id_=TaskExecutionId.generate(),
            name=TaskExecutionName("my-task"),
            body=TaskExecutionBody("task-body"),
            now=_NOW,
        )
        events = task_execution.pull_events()
        assert len(events) == 1
        assert type(events[0]).__name__ == "TaskExecutionCreatedEvent"

    def test_hash_changes_with_content(self) -> None:
        t1 = TaskExecution.create(
            id_=TaskExecutionId.generate(),
            name=TaskExecutionName("task-name"),
            body=TaskExecutionBody("task-body-a"),
            now=_NOW,
        )
        t2 = TaskExecution.create(
            id_=TaskExecutionId.generate(),
            name=TaskExecutionName("task-name"),
            body=TaskExecutionBody("task-body-b"),
            now=_NOW,
        )
        assert t1.hash != t2.hash

    def test_supersede_marks_not_current(self) -> None:
        task_execution = TaskExecution.create(
            id_=TaskExecutionId.generate(),
            name=TaskExecutionName("task-name"),
            body=TaskExecutionBody("task-body"),
            now=_NOW,
        )
        task_execution.supersede()
        assert task_execution.is_current is False
