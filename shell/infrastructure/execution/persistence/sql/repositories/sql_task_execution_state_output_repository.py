from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution_state.repositories.task_execution_state_repository import (
    TaskExecutionStateRepository,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    task_execution_output_payload_entity_to_model,
    task_execution_output_payload_model_to_entity,
)
from sqlalchemy import select

from ..models import TaskExecutionStateOutputModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
        TaskExecutionState,
    )
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlTaskExecutionStateRepository(TaskExecutionStateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionState | None:
        query = (
            select(TaskExecutionStateOutputModel)
            .where(
                TaskExecutionStateOutputModel.task_execution_id == task_execution_id.value,
                TaskExecutionStateOutputModel.is_current.is_(True),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return task_execution_output_payload_model_to_entity(row) if row else None

    async def save(self, payload: TaskExecutionState) -> None:
        model = task_execution_output_payload_entity_to_model(payload)
        await self._session.merge(model)

    async def delete(self, id: object) -> None:
        ...

    async def exists(self, id: object) -> bool:
        ...


__all__ = [
    "SqlTaskExecutionStateRepository",
    "TaskExecutionStateOutputModel",
]
