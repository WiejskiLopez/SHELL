from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
    SessionExecutionId,
)
from shell.domain.execution.aggregates.session_execution_state.repositories.session_execution_state_repository import (
    SessionExecutionStateRepository,
)
from shell.domain.execution.value_objects.state_direction import StateDirection
from shell.infrastructure.platform.persistence.sql.mappers import (
    session_execution_state_entity_to_model,
    session_execution_state_model_to_entity,
)
from sqlalchemy import select

from ..models import SessionExecutionStateModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session_execution_state.session_execution_state import (
        SessionExecutionState,
    )
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlSessionExecutionStateRepository(SessionExecutionStateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_session_execution_id(
        self,
        session_execution_id: SessionExecutionId,
        direction: StateDirection | None = None,
    ) -> SessionExecutionState | None:
        query = select(SessionExecutionStateModel).where(
            SessionExecutionStateModel.session_execution_id == session_execution_id.value,
            SessionExecutionStateModel.is_current.is_(True),
        )
        if direction is not None:
            query = query.where(SessionExecutionStateModel.direction == direction.value)
        query = query.order_by(SessionExecutionStateModel.created_at.desc()).limit(1)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return session_execution_state_model_to_entity(row) if row else None

    async def save(self, payload: SessionExecutionState) -> None:
        existing = await self.get_latest_by_session_execution_id(
            payload.session_execution_id, direction=payload.direction
        )
        if existing is not None:
            existing.supersede()
            old_model = await self._session.get(
                SessionExecutionStateModel, existing.id.value
            )
            if old_model is not None:
                old_model.is_current = existing.is_current.value
        model = session_execution_state_entity_to_model(payload)
        self._session.add(model)

    async def delete(self, id_: object) -> None:
        model = await self._session.get(SessionExecutionStateModel, id_.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id_: object) -> bool:
        query = select(SessionExecutionStateModel).where(
            SessionExecutionStateModel.id == id_.value
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return row is not None
