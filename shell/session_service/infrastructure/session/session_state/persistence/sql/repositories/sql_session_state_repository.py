from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import exists as sa_exists
from sqlalchemy import select

from shell.platform.domain.value_objects.exists_result import ExistsResult
from shell.session_service.domain.session.aggregates.session_state.repositories.session_state_repository import (
    SessionStateRepository,
)
from shell.session_service.infrastructure.session.session_state.persistence.sql.mappers.session_state_change_model import (
    session_state_change_model,
)
from shell.session_service.infrastructure.session.session_state.persistence.sql.mappers.session_state_entity_to_model import (
    session_state_entity_to_model,
)
from shell.session_service.infrastructure.session.session_state.persistence.sql.mappers.session_state_model_to_entity import (
    session_state_model_to_entity,
)

from ..models import SessionStateModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.platform.domain.value_objects.state_direction import StateDirection
    from shell.session_service.domain.session.aggregates.session.value_objects.session_id import (
        SessionId,
    )
    from shell.session_service.domain.session.aggregates.session_state.session_state import (
        SessionState,
    )
    from shell.session_service.domain.session.aggregates.session_state.value_objects.session_state_id import (
        SessionStateId,
    )


class SqlSessionStateRepository(SessionStateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, session_state: SessionState) -> None:
        model = await self._session.get(SessionStateModel, session_state.id.value)
        if model is None:
            model = session_state_entity_to_model(session_state)
            self._session.add(model)
        else:
            session_state_change_model(model, session_state)

    async def get_by_id(self, id_: SessionStateId) -> SessionState | None:
        query = select(SessionStateModel).where(SessionStateModel.id == id_.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        if row is None:
            return None
        return session_state_model_to_entity(row)

    async def list_by_session_id(self, session_id: SessionId) -> list[SessionState]:
        query = select(SessionStateModel).where(SessionStateModel.session_id == session_id.value)
        rows = (await self._session.execute(query)).scalars().all()
        return [session_state_model_to_entity(row) for row in rows]

    async def list_by_session_and_direction(
        self, session_id: SessionId, direction: StateDirection
    ) -> list[SessionState]:
        query = select(SessionStateModel).where(
            SessionStateModel.session_id == session_id.value,
            SessionStateModel.direction == direction.value,
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [session_state_model_to_entity(row) for row in rows]

    async def delete(self, id_: SessionStateId) -> None:
        model = await self._session.get(SessionStateModel, id_.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id_: SessionStateId) -> ExistsResult:
        stmt = select(sa_exists().where(SessionStateModel.id == id_.value))
        result = await self._session.execute(stmt)
        return ExistsResult(result.scalar() or False)


__all__ = [
    "SessionStateModel",
    "SqlSessionStateRepository",
]
