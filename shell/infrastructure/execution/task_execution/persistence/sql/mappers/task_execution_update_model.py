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


def task_execution_update_model(model: TaskExecutionModel, entity: TaskExecution) -> None:
    model.status = entity.status.value if hasattr(entity.status, "value") else entity.status
    model.name = entity.name.value
    model.body = entity.body.value if entity.body else model.body
    model.work_dir = entity.work_dir.value if entity.work_dir else ""
    model.workflow_id = entity.workflow_id.value if entity.workflow_id else None
    model.created_at = _created_at_value(entity.created_at)  # type: ignore[assignment]
    model.deleted_at = _created_at_value(entity.deleted_at)