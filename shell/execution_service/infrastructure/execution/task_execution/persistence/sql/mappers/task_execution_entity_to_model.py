"""SQL ORM model <-> domain entity mappers for TaskExecution aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution_service.infrastructure.execution.task_execution.persistence.sql.models.task_execution import (
    TaskExecutionModel,
)

from ._created_at_value import _created_at_value

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.task_execution.task_execution import (
        TaskExecution,
    )


def task_execution_entity_to_model(task_execution: TaskExecution) -> TaskExecutionModel:
    return TaskExecutionModel(
        id=task_execution.id.value,
        status=task_execution.status.value,
        name=task_execution.name.value,
        work_dir=task_execution.work_dir.value if task_execution.work_dir else "",
        created_at=_created_at_value(task_execution.created_at),
        workflow_id=task_execution.workflow_id.value,
        deleted_at=_created_at_value(task_execution.deleted_at),
    )
