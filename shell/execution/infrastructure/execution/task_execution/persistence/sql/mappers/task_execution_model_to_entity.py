"""SQL ORM model <-> domain entity mappers for TaskExecution aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.execution.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.execution.domain.execution.aggregates.task_execution.value_objects.task_name import (
    TaskName,
)
from shell.execution.domain.execution.aggregates.task_execution.value_objects.work_dir import (
    WorkDir,
)
from shell.execution.domain.execution.aggregates.workflow.value_objects.workflow_id import (
    WorkflowId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.infrastructure.persistence.sql.mappers._ensure_utc import (
    ensure_utc as _ensure_utc,
)

if TYPE_CHECKING:
    from shell.execution.infrastructure.execution.task_execution.persistence.sql.models.task_execution import (
        TaskExecutionModel,
    )


def task_execution_model_to_entity(task_execution_model: TaskExecutionModel) -> TaskExecution:
    return TaskExecution.restore(
        id=TaskExecutionId(task_execution_model.id),
        name=TaskName(task_execution_model.name),
        created_at=CreatedAt.from_datetime(_ensure_utc(task_execution_model.created_at)),
        work_dir=WorkDir(task_execution_model.work_dir),
        workflow_id=WorkflowId(task_execution_model.workflow_id),
        deleted_at=(DeletedAt.from_datetime(task_execution_model.deleted_at)),
    )
