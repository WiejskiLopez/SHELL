from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution_state_input.repositories.task_execution_state_input_repository import (
    TaskExecutionStateInputRepository,
)
from shell.domain.execution.value_objects.ids import (
    TaskExecutionId,  # noqa: TC002 — TaskExecutionId używany w konstruktorach w repozytorium
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    task_execution_input_payload_entity_to_model,
    task_execution_input_payload_model_to_entity,
)
from sqlalchemy import select

from ..models import TaskExecutionStateInputModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution_state_input.task_execution_state_input import (
        TaskExecutionStateInput,
    )
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlTaskExecutionStateInputRepository(TaskExecutionStateInputRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionStateInput | None:
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

    async def save(self, payload: TaskExecutionStateInput) -> None:
        existing = await self.get_latest_by_task_id(payload.task_execution_id)
        if existing is not None:
            existing.supersede()
            old_model = task_execution_input_payload_entity_to_model(existing)
            await self._session.merge(old_model)
        model = task_execution_input_payload_entity_to_model(payload)
        self._session.add(model)


__all__ = [
    "SqlTaskExecutionStateInputRepository",
    "TaskExecutionStateInputModel",
]
