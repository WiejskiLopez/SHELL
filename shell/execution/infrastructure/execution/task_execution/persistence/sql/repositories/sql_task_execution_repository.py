from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.execution.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.execution.infrastructure.execution.task_execution.persistence.sql.mappers import (
    task_execution_entity_to_model,
    task_execution_model_to_entity,
    task_execution_update_model,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult

from ..models import TaskExecutionModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.execution.domain.execution.aggregates.task_execution.task_execution import (
        TaskExecution,
    )
    from shell.execution.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.execution.domain.execution.aggregates.task_execution.value_objects.task_execution_name import (
        TaskExecutionName,  # noqa: TC002 — TaskExecutionName używany w konstruktorach w repozytorium
    )
    from shell.execution.domain.execution.aggregates.workflow.value_objects.workflow_id import (
        WorkflowId,
    )


class SqlTaskExecutionRepository(TaskExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, task_execution_id: TaskExecutionId) -> TaskExecution | None:
        query = select(TaskExecutionModel).where(TaskExecutionModel.id == task_execution_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return task_execution_model_to_entity(row) if row else None

    async def get_by_name(self, name: TaskExecutionName) -> TaskExecution | None:
        query = select(TaskExecutionModel).where(TaskExecutionModel.name == name.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return task_execution_model_to_entity(row) if row else None

    async def get_current_by_id(self, id: TaskExecutionId) -> TaskExecution | None:
        return await self.get_by_id(id)

    async def get_current_by_name(self, name: TaskExecutionName) -> TaskExecution | None:
        return await self.get_by_name(name)

    async def save(self, task_execution: TaskExecution) -> None:
        model = await self._session.get(TaskExecutionModel, task_execution.id.value)
        if model is None:
            model = task_execution_entity_to_model(task_execution)
            self._session.add(model)
        else:
            task_execution_update_model(model, task_execution)

    async def get_by_workflow_id(self, workflow_id: WorkflowId) -> list[TaskExecution]:
        query = select(TaskExecutionModel).where(
            TaskExecutionModel.workflow_id == workflow_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [task_execution_model_to_entity(row) for row in rows]

    async def list_current(self) -> list[TaskExecution]:
        rows = (await self._session.execute(select(TaskExecutionModel))).scalars().all()
        return [task_execution_model_to_entity(row) for row in rows]

    async def delete(self, id: TaskExecutionId) -> None:
        model = await self._session.get(TaskExecutionModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: TaskExecutionId) -> ExistsResult:
        entity = await self.get_by_id(id)
        return ExistsResult(entity is not None)
