from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import exists as sa_exists
from sqlalchemy import select

from shell.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.infrastructure.session.session.persistence.sql.mappers import (
    session_entity_to_model,
    session_model_to_entity,
    session_update_model,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult

from ..models import SessionModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.session.aggregates.session import Session
    from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
    from shell.domain.session.value_objects.user_id_ref import UserIdRef


class SqlSessionRepository(SessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, session: Session) -> None:
        model = await self._session.get(SessionModel, session.id.value)
        if model is None:
            model = session_entity_to_model(session)
            self._session.add(model)
        else:
            session_update_model(model, session)

    async def get_by_id(self, session_id: SessionId) -> Session | None:
        query = select(SessionModel).where(SessionModel.id == session_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        if row is None:
            return None
        return session_model_to_entity(row)

    async def get_open_by_user_id(self, user_id: UserIdRef) -> Session | None:
        query = (
            select(SessionModel)
            .where(
                SessionModel.user_id == user_id.value,
                SessionModel.status == "OPEN",
                SessionModel.deleted_at.is_(None),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        if row is None:
            return None
        return session_model_to_entity(row)

    async def delete(self, id: SessionId) -> None:
        model = await self._session.get(SessionModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: SessionId) -> ExistsResult:
        stmt = select(sa_exists().where(SessionModel.id == id.value))
        result = await self._session.execute(stmt)
        return ExistsResult(result.scalar() or False)


__all__ = [
    "SessionModel",
    "SqlSessionRepository",
]
