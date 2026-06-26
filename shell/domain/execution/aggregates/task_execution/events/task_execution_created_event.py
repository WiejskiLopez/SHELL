from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import TaskExecutionId
from shell.domain.execution.value_objects.skill_payload import SkillPayload
from shell.domain.execution.value_objects.task_description import TaskDescription
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class TaskExecutionCreatedEvent(DomainEvent):
    task_execution_id: TaskExecutionId
    task_execution_name: TaskExecutionName
    description: TaskDescription = field(default_factory=lambda: TaskDescription("default"))
    skills: list[SkillPayload] | None = None

    @classmethod
    def now(
        cls,
        task_execution_id: TaskExecutionId,
        task_execution_name: TaskExecutionName,
        now: datetime,
        description: str = "default",
        skills: list[SkillPayload] | None = None,
    ) -> TaskExecutionCreatedEvent:
        return cls(
            occurred_at=now,
            task_execution_id=task_execution_id,
            task_execution_name=task_execution_name,
            description=TaskDescription(description),
            skills=skills,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, object], schema_version: int = 1
    ) -> Self:
        raw_skills = payload.get("skills")
        parsed_skills = None
        if raw_skills is not None:
            from shell.domain.execution.value_objects.skill_payload import SkillPayload
            parsed_skills = [SkillPayload(s) if isinstance(s, dict) else s for s in raw_skills]
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            task_execution_id=TaskExecutionId(payload.get("task_execution_id")),
            task_execution_name=TaskExecutionName(payload.get("task_execution_name", "")),
            description=TaskDescription(payload.get("description", "")),
            skills=parsed_skills,
        )
