from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.value_objects.ids import TaskExecutionStateInputId

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class TaskExecutionStateInput:
    id: TaskExecutionStateInputId
    task_execution_id: TaskExecutionId
    payload: dict[str, Any]
    created_at: datetime
