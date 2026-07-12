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


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _created_at_value(dt: CreatedAt | DeletedAt | datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.value if hasattr(dt, "value") else dt


def task_execution_model_to_entity(task_execution_model: TaskExecutionModel) -> TaskExecution:
    body = TaskExecutionBody(task_execution_model.body) if task_execution_model.body else None
    return TaskExecution.restore(
        id=TaskExecutionId(task_execution_model.id),
        name=TaskName(task_execution_model.name),
        body=body,
        created_at=CreatedAt.from_datetime(_ensure_utc(task_execution_model.created_at)),
        work_dir=WorkDir(task_execution_model.work_dir),
        workflow_id=(
            WorkflowId(task_execution_model.workflow_id)
            if task_execution_model.workflow_id
            else None
        ),
        deleted_at=(
            DeletedAt.from_datetime(task_execution_model.deleted_at)
            if task_execution_model.deleted_at
            else None
        ),
    )


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


def task_execution_update_model(model: TaskExecutionModel, entity: TaskExecution) -> None:
    model.status = entity.status.value if hasattr(entity.status, "value") else entity.status
    model.name = entity.name.value
    model.body = entity.body.value if entity.body else model.body
    model.work_dir = entity.work_dir.value if entity.work_dir else ""
    model.workflow_id = entity.workflow_id.value if entity.workflow_id else None
    model.created_at = _created_at_value(entity.created_at)  # type: ignore[assignment]
    model.deleted_at = _created_at_value(entity.deleted_at)
