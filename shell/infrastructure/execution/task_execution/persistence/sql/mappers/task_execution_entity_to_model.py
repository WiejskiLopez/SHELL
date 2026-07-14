"""SQL ORM model <-> domain entity mappers for TaskExecution aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.execution.task_execution.persistence.sql.models.task_execution import (
    TaskExecutionModel,
)

from ._created_at_value import _created_at_value

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution


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
