from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.value_objects.event_output import EventOutput
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True)
class TaskExecutionCompletedEvent(DomainEvent):
    task_execution_id: TaskExecutionId
    task_execution_name: TaskExecutionName
    output: EventOutput = field(default_factory=lambda: EventOutput("default"))

    @classmethod
    def now(
        cls,
        task_execution_id: TaskExecutionId,
        task_execution_name: TaskExecutionName,
        output: str = "default",
        now: CreatedAt | None = None,
    ) -> TaskExecutionCompletedEvent:
        return cls(
            occurred_at=now or CreatedAt.now(),
            task_execution_id=task_execution_id,
            task_execution_name=task_execution_name,
            output=EventOutput(output),
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            task_execution_id=TaskExecutionId(payload["task_execution_id"]),
            task_execution_name=TaskExecutionName(payload.get("task_execution_name", "")),
            output=EventOutput(payload.get("output", "")),
        )
