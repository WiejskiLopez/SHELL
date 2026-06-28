from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session_execution.repositories.session_execution_repository import (
    SessionExecutionRepository,
)
from shell.domain.execution.value_objects.ids import (
    SessionExecutionId,
    UserExecutionId,
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    session_execution_entity_to_model,
    session_execution_model_to_entity,
    session_execution_update_model,
)
from sqlalchemy import select

from ..models import SessionExecutionModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session_execution import SessionExecution
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlSessionExecutionRepository(SessionExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: SessionExecutionId) -> SessionExecution | None:
        query = select(SessionExecutionModel).where(SessionExecutionModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return session_execution_model_to_entity(row) if row else None

    async def get_by_user_execution_id(
        self, user_execution_id: UserExecutionId
    ) -> list[SessionExecution]:
        query = select(SessionExecutionModel).where(
            SessionExecutionModel.user_execution_id == user_execution_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [session_execution_model_to_entity(row) for row in rows if row]

    async def save(self, session_execution: SessionExecution) -> None:
        model = await self._session.get(SessionExecutionModel, session_execution.id.value)
        if model is None:
            model = session_execution_entity_to_model(session_execution)
            self._session.add(model)
        else:
            session_execution_update_model(model, session_execution)

    async def delete(self, id: SessionExecutionId) -> None:
        model = await self._session.get(SessionExecutionModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: SessionExecutionId) -> bool:
        query = select(SessionExecutionModel).where(SessionExecutionModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return row is not None
