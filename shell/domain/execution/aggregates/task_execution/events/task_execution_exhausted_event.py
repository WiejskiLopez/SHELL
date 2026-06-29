from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.value_objects.max_planning_cycles import MaxPlanningCycles
from shell.domain.execution.value_objects.planning_cycle import PlanningCycle
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True)
class TaskExecutionExhaustedEvent(DomainEvent):
    task_execution_id: TaskExecutionId
    current_cycle: PlanningCycle
    max_planning_cycles: MaxPlanningCycles

    @classmethod
    def now(
        cls,
        task_execution_id: TaskExecutionId,
        current_cycle: PlanningCycle,
        max_planning_cycles: MaxPlanningCycles,
        now: CreatedAt,
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
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            task_execution_id=TaskExecutionId(payload["task_execution_id"]),
            current_cycle=PlanningCycle(payload["current_cycle"]),
            max_planning_cycles=MaxPlanningCycles(payload["max_planning_cycles"]),
        )
