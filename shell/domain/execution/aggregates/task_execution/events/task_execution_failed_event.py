from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import TaskExecutionId
from shell.domain.execution.value_objects.reason import Reason
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class TaskExecutionFailedEvent(DomainEvent):
    task_execution_id: TaskExecutionId
    reason: Reason

    @classmethod
    def now(
        cls,
        task_execution_id: TaskExecutionId,
        reason: Reason,
        now: datetime,
    ) -> TaskExecutionFailedEvent:
        return cls(
            occurred_at=now,
            task_execution_id=task_execution_id,
            reason=reason,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            task_execution_id=TaskExecutionId(payload.get("task_execution_id")),
            reason=Reason(payload.get("reason", "")),
        )
