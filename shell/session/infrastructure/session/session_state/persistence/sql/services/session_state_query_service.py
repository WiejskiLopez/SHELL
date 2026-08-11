from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.platform.types import JsonStr
from shell.session.application.session.session_state.dto.session_state import SessionStateDto
from shell.session.infrastructure.session.session_state.persistence.sql.models.session_state import (
    SessionStateModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SessionStateQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, session_state_id: str) -> SessionStateDto | None:
        async with self._session_factory() as session:
            stmt = select(SessionStateModel).where(SessionStateModel.id == session_state_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return SessionStateDto(
                id=model.id,
                session_id=model.session_id,
                direction=model.direction,
                state_data=JsonStr(json.dumps(dict(model.state_data))),
                created_at=model.created_at,
            )
