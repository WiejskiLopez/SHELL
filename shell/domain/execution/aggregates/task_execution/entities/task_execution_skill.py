from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_skill_id import (
    TaskExecutionSkillId,
)
from shell.domain.execution.value_objects.skill_payload import SkillPayload

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class TaskExecutionSkill:
    id: TaskExecutionSkillId
    task_execution_id: TaskExecutionId
    payload: SkillPayload
    created_at: datetime
