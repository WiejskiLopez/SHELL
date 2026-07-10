from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.execution.aggregates.user_execution.repositories.user_execution_repository import (
    UserExecutionRepository,
)
from shell.infrastructure.execution.user_execution.persistence.sql.mappers import (
    user_execution_entity_to_model,
    user_execution_model_to_entity,
    user_execution_update_model,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult

from ..models import UserExecutionModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.execution.aggregates.user_execution import UserExecution
    from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
        UserExecutionId,
    )


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

    async def delete(self, id: UserExecutionId, now: datetime | None = None) -> None:
        if now is None:
            now = datetime.now(tz=UTC)
        model = await self._session.get(UserExecutionModel, id.value)
        if model is not None:
            model.deleted_at = now

    async def exists(self, id: UserExecutionId) -> ExistsResult:
        query = select(UserExecutionModel).where(UserExecutionModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ExistsResult(row is not None)
