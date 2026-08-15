from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.execution_service.application.execution.session_execution.dto.session_execution_state import (
    SessionExecutionStateDto,
)
from shell.execution_service.infrastructure.execution.session_execution_state.persistence.sql.models.session_execution_state import (
    SessionExecutionStateModel,
)
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SessionExecutionStateQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, session_execution_state_id: str) -> SessionExecutionStateDto | None:
        async with self._session_factory() as session:
            stmt = select(SessionExecutionStateModel).where(
                SessionExecutionStateModel.id == session_execution_state_id
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return SessionExecutionStateDto(
                id=model.id,
                session_execution_id=model.session_execution_id,
                direction=model.direction,
                state_data=JsonStr(json.dumps(dict(model.state_data))),
                created_at=model.created_at,
            )
