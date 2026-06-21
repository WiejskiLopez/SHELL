from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution.ports.task_execution_repository import (
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
)
from sqlalchemy import select

from ..models import TaskExecutionModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SqlTaskExecutionRepository(TaskExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, task_execution_id: TaskExecutionId) -> TaskExecution | None:
        query = select(TaskExecutionModel).where(TaskExecutionModel.id == task_execution_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return task_execution_model_to_entity(row) if row else None

    async def get_by_name(self, name: TaskExecutionName) -> TaskExecution | None:
        query = (
            select(TaskExecutionModel)
            .where(TaskExecutionModel.name == name.value)
            .order_by(TaskExecutionModel.version.desc())
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return task_execution_model_to_entity(row) if row else None

    async def get_current_by_id(self, id: TaskExecutionId) -> TaskExecution | None:
        logger.info("Querying current Task by id=%s", id.value)
        query = (
            select(TaskExecutionModel)
            .where(
                TaskExecutionModel.id == id.value,
                TaskExecutionModel.is_current.is_(True),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        if not row:
            logger.info("No current Task found for id=%s", id.value)
            return None

        logger.info(
            "TaskExecutionModel found: id=%s name=%s is_current=%s",
            row.id,
            row.name,
            row.is_current,
        )
        return task_execution_model_to_entity(row)

    async def get_current_by_name(self, name: TaskExecutionName) -> TaskExecution | None:
        logger.info("Querying current Task by name=%s", name.value)
        query = (
            select(TaskExecutionModel)
            .where(TaskExecutionModel.name == name.value, TaskExecutionModel.is_current.is_(True))
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        if not row:
            logger.info("No current Task found for name=%s", name.value)
            return None

        logger.info(
            "TaskExecutionModel found: id=%s name=%s is_current=%s",
            row.id,
            row.name,
            row.is_current,
        )
        return task_execution_model_to_entity(row)

    async def save(self, task_execution: TaskExecution) -> None:
        model = task_execution_entity_to_model(task_execution)
        await self._session.merge(model)

    async def get_by_workflow_id(self, workflow_id: WorkflowId) -> list[TaskExecution]:
        query = select(TaskExecutionModel).where(
            TaskExecutionModel.workflow_id == workflow_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [task_execution_model_to_entity(row) for row in rows]

    async def list_current(self) -> list[TaskExecution]:
        query = select(TaskExecutionModel).where(TaskExecutionModel.is_current.is_(True))
        rows = (await self._session.execute(query)).scalars().all()
        return [task_execution_model_to_entity(row) for row in rows]
