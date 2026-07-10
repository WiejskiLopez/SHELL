from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution.value_objects.task_description import (
    TaskDescription,
)
from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.value_objects.skill_data import (
        SkillData,
    )
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_name import (
        TaskExecutionName,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class TaskExecutionCreatedEvent(DomainEvent):
    task_execution_id: TaskExecutionId
    task_execution_name: TaskExecutionName
    description: TaskDescription = field(default_factory=lambda: TaskDescription("default"))
    skills: list[SkillData] | None = None

    @classmethod
    def now(
        cls,
        task_execution_id: TaskExecutionId,
        task_execution_name: TaskExecutionName,
        now: CreatedAt,
        description: str = "default",
        skills: list[SkillData] | None = None,
    ) -> TaskExecutionCreatedEvent:
        return cls(
            occurred_at=now,
            task_execution_id=task_execution_id,
            task_execution_name=task_execution_name,
            description=TaskDescription(description),
            skills=skills,
        )
