"""SQL ORM model <-> domain entity mappers for TaskExecution aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_body import (
    TaskExecutionBody,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_name import TaskName
from shell.domain.execution.aggregates.task_execution.value_objects.work_dir import WorkDir
from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.infrastructure.execution.task_execution.persistence.sql.models.task_execution import (
    TaskExecutionModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt


def _created_at_value(dt: CreatedAt | DeletedAt | datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.value if hasattr(dt, "value") else dt

