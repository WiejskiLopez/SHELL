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


def task_execution_entity_to_model(task_execution: TaskExecution) -> TaskExecutionModel:
    return TaskExecutionModel(
        id=task_execution.id.value,
        name=task_execution.name.value,
        body=task_execution.body.value if task_execution.body else "",
        work_dir=task_execution.work_dir.value if task_execution.work_dir else "",
        created_at=_created_at_value(task_execution.created_at),
        workflow_id=task_execution.workflow_id.value if task_execution.workflow_id else None,
        deleted_at=_created_at_value(task_execution.deleted_at),
    )

