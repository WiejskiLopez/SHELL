from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.task_execution.task_execution_id import TaskExecutionId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class TaskExecutionExhaustedEvent(DomainEvent):
    task_execution_id: TaskExecutionId
    current_cycle: int
    max_planning_cycles: int

    @classmethod
    def now(
        cls,
        task_execution_id: TaskExecutionId,
        current_cycle: int,
        max_planning_cycles: int,
        now: datetime,
    ) -> TaskExecutionExhaustedEvent:
        return cls(
            occurred_at=now,
            task_execution_id=task_execution_id,
            current_cycle=current_cycle,
            max_planning_cycles=max_planning_cycles,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            task_execution_id=TaskExecutionId(payload["task_execution_id"]),
            current_cycle=payload["current_cycle"],
            max_planning_cycles=payload["max_planning_cycles"],
        )
