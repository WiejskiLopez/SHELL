"""SQL ORM model <-> domain entity mappers for TaskExecution aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._created_at_value import _created_at_value

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.task_execution.task_execution import (
        TaskExecution,
    )
    from shell.execution_service.infrastructure.execution.task_execution.persistence.sql.models.task_execution import (
        TaskExecutionModel,
    )


def task_execution_update_model(model: TaskExecutionModel, entity: TaskExecution) -> None:
    model.status = entity.status.value if hasattr(entity.status, "value") else entity.status
    model.name = entity.name.value
    model.work_dir = entity.work_dir.value if entity.work_dir else ""
    model.workflow_id = entity.workflow_id.value
    model.created_at = _created_at_value(entity.created_at)  # type: ignore[assignment]
    model.deleted_at = _created_at_value(entity.deleted_at)
