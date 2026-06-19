from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.value_objects.ids import TaskExecutionId

from ..mappers import (
    task_execution_input_payload_entity_to_model,
    task_execution_input_payload_model_to_entity,
)
from ..models import TaskExecutionInputPayloadModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.aggregates.task_execution_input_payload import (
        TaskExecutionInputPayload,
    )


class SqlTaskExecutionInputPayloadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionInputPayload | None:
        query = (
            select(TaskExecutionInputPayloadModel)
            .where(
                TaskExecutionInputPayloadModel.task_execution_id == task_execution_id.value,
                TaskExecutionInputPayloadModel.is_current.is_(True),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return task_execution_input_payload_model_to_entity(row) if row else None

    async def save(self, payload: TaskExecutionInputPayload) -> None:
        model = task_execution_input_payload_entity_to_model(payload)
        await self._session.merge(model)
