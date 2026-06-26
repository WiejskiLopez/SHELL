from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import TaskExecutionId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class TaskExecutionTimeoutExpiredEvent(DomainEvent):
    task_execution_id: TaskExecutionId

    @classmethod
    def now(
        cls,
        task_execution_id: TaskExecutionId,
        now: datetime,
    ) -> TaskExecutionTimeoutExpiredEvent:
        return cls(
            occurred_at=now,
            task_execution_id=task_execution_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            task_execution_id=TaskExecutionId(payload.get("task_execution_id")),
        )
