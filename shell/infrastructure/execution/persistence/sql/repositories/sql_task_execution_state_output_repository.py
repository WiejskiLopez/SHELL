from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution_state_output.ports.task_execution_state_output_repository import (
    TaskExecutionStateOutputRepository,
)
from shell.domain.execution.value_objects.ids import (
    TaskExecutionId,  # noqa: TC002 — TaskExecutionId używany w konstruktorach w repozytorium
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    task_execution_output_payload_entity_to_model,
    task_execution_output_payload_model_to_entity,
)
from sqlalchemy import select

from ..models import TaskExecutionStateOutputModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution_state_output.task_execution_state_output import (
        TaskExecutionStateOutput,
    )
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlTaskExecutionStateOutputRepository(TaskExecutionStateOutputRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionStateOutput | None:
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

    async def save(self, payload: TaskExecutionStateOutput) -> None:
        model = task_execution_output_payload_entity_to_model(payload)
        await self._session.merge(model)


__all__ = [
    "SqlTaskExecutionStateOutputRepository",
    "TaskExecutionStateOutputModel",
]
