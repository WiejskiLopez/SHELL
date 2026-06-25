from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution_state.repositories.task_execution_state_repository import (
    TaskExecutionStateRepository,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    task_execution_input_payload_entity_to_model,
    task_execution_input_payload_model_to_entity,
)
from sqlalchemy import select

from ..models import TaskExecutionStateInputModel

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
            select(TaskExecutionStateInputModel)
            .where(
                TaskExecutionStateInputModel.task_execution_id == task_execution_id.value,
                TaskExecutionStateInputModel.is_current.is_(True),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return task_execution_input_payload_model_to_entity(row) if row else None

    async def save(self, payload: TaskExecutionState) -> None:
        existing = await self.get_latest_by_task_id(payload.task_execution_id)
        if existing is not None:
            existing.supersede()
            old_model = task_execution_input_payload_entity_to_model(existing)
            await self._session.merge(old_model)
        model = task_execution_input_payload_entity_to_model(payload)
        self._session.add(model)

    async def delete(self, id: object) -> None:
        ...

    async def exists(self, id: object) -> bool:
        ...


__all__ = [
    "SqlTaskExecutionStateRepository",
    "TaskExecutionStateInputModel",
]
