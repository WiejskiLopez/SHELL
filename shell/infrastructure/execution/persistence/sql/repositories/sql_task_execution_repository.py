from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.value_objects.ids import (  # noqa: TC002 — TaskExecutionId i WorkflowId używane w konstruktorach w repozytorium
    TaskExecutionId,
    WorkflowId,
)
from shell.domain.execution.value_objects.task_execution_name import (
    TaskExecutionName,  # noqa: TC002 — TaskExecutionName używany w konstruktorach w repozytorium
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    task_execution_entity_to_model,
    task_execution_model_to_entity,
    task_execution_update_model,
)
from sqlalchemy import select

from ..models import TaskExecutionModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
    from sqlalchemy.ext.asyncio import AsyncSession


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
