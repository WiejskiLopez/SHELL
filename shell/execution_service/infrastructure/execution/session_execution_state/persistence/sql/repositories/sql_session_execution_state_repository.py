from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.execution_service.domain.execution.aggregates.session_execution_state.repositories.session_execution_state_repository import (
    SessionExecutionStateRepository,
)
from shell.execution_service.infrastructure.execution.session_execution_state.persistence.sql.mappers import (
    session_execution_state_entity_to_model,
    session_execution_state_model_to_entity,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult

from ..models import SessionExecutionStateModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.execution_service.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
        SessionExecutionId,
    )
    from shell.execution_service.domain.execution.aggregates.session_execution_state.session_execution_state import (
        SessionExecutionState,
    )
    from shell.platform.domain.value_objects.state_direction import StateDirection


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
            old_model = await self._session.get(SessionExecutionStateModel, existing.id.value)
            if old_model is not None:
                await self._session.delete(old_model)
        model = session_execution_state_entity_to_model(payload)
        self._session.add(model)

    async def delete(self, id_: object, now: datetime | None = None) -> None:
        if now is None:
            now = datetime.now(tz=UTC)
        model = await self._session.get(SessionExecutionStateModel, getattr(id_, "value", id_))
        if model is not None:
            model.deleted_at = now

    async def exists(self, id_: object) -> ExistsResult:
        query = select(SessionExecutionStateModel).where(
            SessionExecutionStateModel.id == getattr(id_, "value", id_)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ExistsResult(row is not None)
