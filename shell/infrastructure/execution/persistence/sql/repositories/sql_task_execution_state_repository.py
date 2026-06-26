from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.aggregates.task_execution_state.repositories.task_execution_state_repository import (
    TaskExecutionStateRepository,
)
from shell.domain.execution.value_objects.state_kind import StateKind
from shell.infrastructure.platform.persistence.sql.mappers import (
    task_execution_state_entity_to_model,
    task_execution_state_model_to_entity,
)
from sqlalchemy import select

from ..models import TaskExecutionStateModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution_state.value_objects.task_execution_state_id import (
        TaskExecutionStateId,
    )
    from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
        TaskExecutionState,
    )
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlTaskExecutionStateRepository(TaskExecutionStateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_task_id(
        self,
        task_execution_id: TaskExecutionId,
        kind: StateKind | None = None,
    ) -> TaskExecutionState | None:
        query = select(TaskExecutionStateModel).where(
            TaskExecutionStateModel.task_execution_id == task_execution_id.value,
            TaskExecutionStateModel.is_current.is_(True),
        )
        if kind is not None:
            query = query.where(TaskExecutionStateModel.kind == kind.value)
        query = query.order_by(TaskExecutionStateModel.created_at.desc()).limit(1)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return task_execution_state_model_to_entity(row) if row else None

    async def save(self, payload: TaskExecutionState) -> None:
        existing = await self.get_latest_by_task_id(payload.task_execution_id, kind=payload.kind)
        if existing is not None:
            existing.supersede()
            old_model = await self._session.get(TaskExecutionStateModel, existing.id.value)
            if old_model is not None:
                old_model.is_current = existing.is_current.value
        model = task_execution_state_entity_to_model(payload)
        self._session.add(model)

    async def delete(self, id_: TaskExecutionStateId) -> None:
        model = await self._session.get(TaskExecutionStateModel, id_.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id_: TaskExecutionStateId) -> bool:
        query = select(TaskExecutionStateModel).where(TaskExecutionStateModel.id == id_.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return row is not None
