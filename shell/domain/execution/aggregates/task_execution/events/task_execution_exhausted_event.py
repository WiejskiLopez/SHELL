from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.execution.value_objects.max_planning_cycles import MaxPlanningCycles
    from shell.domain.execution.value_objects.planning_cycle import PlanningCycle
    from shell.domain.platform.value_objects.created_at import CreatedAt


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
