from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.domain.execution.aggregates.user_execution_state.repositories.user_execution_state_repository import (
    UserExecutionStateRepository,
)
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.infrastructure.execution.persistence.sql.mappers import (
    user_execution_state_entity_to_model,
    user_execution_state_model_to_entity,
)
from sqlalchemy import select

from ..models import UserExecutionStateModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.user_execution_state.user_execution_state import (
        UserExecutionState,
    )
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlUserExecutionStateRepository(UserExecutionStateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_user_execution_id(
        self,
        user_execution_id: UserExecutionId,
        direction: StateDirection | None = None,
    ) -> UserExecutionState | None:
        query = select(UserExecutionStateModel).where(
            UserExecutionStateModel.user_execution_id == user_execution_id.value,
            UserExecutionStateModel.is_current.is_(True),
        )
        if direction is not None:
            query = query.where(UserExecutionStateModel.direction == direction.value)
        query = query.order_by(UserExecutionStateModel.created_at.desc()).limit(1)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return user_execution_state_model_to_entity(row) if row else None

    async def save(self, payload: UserExecutionState) -> None:
        existing = await self.get_latest_by_user_execution_id(
            payload.user_execution_id, direction=payload.direction
        )
        if existing is not None:
            existing.supersede()
            old_model = await self._session.get(
                UserExecutionStateModel, existing.id.value
            )
            if old_model is not None:
                old_model.is_current = existing.is_current.value
        model = user_execution_state_entity_to_model(payload)
        self._session.add(model)

    async def delete(self, id_: object) -> None:
        model = await self._session.get(UserExecutionStateModel, id_.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id_: object) -> bool:
        query = select(UserExecutionStateModel).where(UserExecutionStateModel.id == id_.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return row is not None
