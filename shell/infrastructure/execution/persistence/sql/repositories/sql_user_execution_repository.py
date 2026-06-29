from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.user_execution.repositories.user_execution_repository import (
    UserExecutionRepository,
)
from shell.domain.execution.value_objects.ids import UserExecutionId
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.infrastructure.execution.persistence.sql.mappers import (
    user_execution_entity_to_model,
    user_execution_model_to_entity,
    user_execution_update_model,
)
from sqlalchemy import select

from ..models import UserExecutionModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.user_execution import UserExecution
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlUserExecutionRepository(UserExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: UserExecutionId) -> UserExecution | None:
        query = select(UserExecutionModel).where(UserExecutionModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return user_execution_model_to_entity(row) if row else None

    async def save(self, user_execution: UserExecution) -> None:
        model = await self._session.get(UserExecutionModel, user_execution.id.value)
        if model is None:
            model = user_execution_entity_to_model(user_execution)
            self._session.add(model)
        else:
            user_execution_update_model(model, user_execution)

    async def delete(self, id: UserExecutionId) -> None:
        model = await self._session.get(UserExecutionModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: UserExecutionId) -> ExistsResult:
        query = select(UserExecutionModel).where(UserExecutionModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ExistsResult(row is not None)
