from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session.ports.session_repository import SessionRepository
from shell.domain.execution.value_objects.ids import (
    SessionId,  # noqa: TC002 — SessionId używany w konstruktorach w repozytorium
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    session_entity_to_model,
    session_model_to_entity,
)
from sqlalchemy import select

from ..models import SessionModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session import Session
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlSessionRepository(SessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, session: Session) -> None:
        model = session_entity_to_model(session)
        await self._session.merge(model)

    async def get_by_id(self, session_id: SessionId) -> Session | None:
        query = select(SessionModel).where(SessionModel.id == session_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        if row is None:
            return None
        return session_model_to_entity(row)


__all__ = [
    "SessionModel",
    "SqlSessionRepository",
]
