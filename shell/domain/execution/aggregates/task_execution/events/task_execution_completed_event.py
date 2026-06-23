from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.task_execution.task_execution_id import TaskExecutionId
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class TaskExecutionCompletedEvent(DomainEvent):
    task_execution_id: TaskExecutionId
    task_execution_name: TaskExecutionName
    output: str = ""

    @classmethod
    def now(
        cls,
        task_execution_id: TaskExecutionId,
        task_execution_name: TaskExecutionName,
        output: str = "",
        now: datetime | None = None,
    ) -> TaskExecutionCompletedEvent:
        from datetime import datetime as _dt
        return cls(
            occurred_at=now or _dt.now(),
            task_execution_id=task_execution_id,
            task_execution_name=task_execution_name,
            output=output,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            task_execution_id=TaskExecutionId(payload["task_execution_id"]),
            task_execution_name=TaskExecutionName(payload.get("task_execution_name", "")),
            output=payload.get("output", ""),
        )
