from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.execution.aggregates.task_execution_state.repositories.task_execution_state_repository import (
    TaskExecutionStateRepository,
)
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.infrastructure.execution.persistence.sql.mappers import (
    task_execution_state_entity_to_model,
    task_execution_state_model_to_entity,
)

from ..models import TaskExecutionStateModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
        TaskExecutionState,
    )
    from shell.domain.platform.value_objects.state_direction import StateDirection


class SqlTaskExecutionStateRepository(TaskExecutionStateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_task_id(
        self,
        task_execution_id: TaskExecutionId,
        direction: StateDirection | None = None,
    ) -> TaskExecutionState | None:
        query = select(TaskExecutionStateModel).where(
            TaskExecutionStateModel.task_execution_id == task_execution_id.value,
            TaskExecutionStateModel.is_current.is_(True),
        )
        if direction is not None:
            query = query.where(TaskExecutionStateModel.direction == direction.value)
        query = query.order_by(TaskExecutionStateModel.created_at.desc()).limit(1)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return task_execution_state_model_to_entity(row) if row else None

    async def save(self, payload: TaskExecutionState) -> None:
        existing = await self.get_latest_by_task_id(
            payload.task_execution_id, direction=payload.direction
        )
        if existing is not None:
            existing.supersede()
            old_model = await self._session.get(TaskExecutionStateModel, existing.id.value)
            if old_model is not None:
                old_model.is_current = existing.is_current
        model = task_execution_state_entity_to_model(payload)
        self._session.add(model)

    async def delete(self, id_: object, now: datetime | None = None) -> None:
        if now is None:
            now = datetime.now(tz=UTC)
        model = await self._session.get(TaskExecutionStateModel, getattr(id_, "value", id_))
        if model is not None:
            model.deleted_at = now

    async def exists(self, id_: object) -> ExistsResult:
        query = select(TaskExecutionStateModel).where(
            TaskExecutionStateModel.id == getattr(id_, "value", id_)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ExistsResult(row is not None)
