from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.domain.user.aggregates.user_state.repositories.user_state_repository import (
    UserStateRepository,
)
from shell.infrastructure.user.persistence.sql.mappers import (
    user_state_entity_to_model,
    user_state_model_to_entity,
)

from ..models import UserStateModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.platform.value_objects.state_direction import StateDirection
    from shell.domain.user.aggregates.user_state.user_state import UserState
    from shell.domain.user.aggregates.user_state.value_objects.user_state_id import UserStateId
    from shell.domain.user.value_objects.user_id import UserId


class SqlUserStateRepository(UserStateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_state_id: UserStateId) -> UserState | None:
        query = select(UserStateModel).where(UserStateModel.id == user_state_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return user_state_model_to_entity(row) if row else None

    async def get_current_by_user_id_and_direction(
        self, user_id: UserId, direction: StateDirection
    ) -> UserState | None:
        query = (
            select(UserStateModel)
            .where(
                UserStateModel.user_id == user_id.value,
                UserStateModel.direction == direction.value,
                UserStateModel.is_current.is_(True),
            )
            .order_by(UserStateModel.created_at.desc())
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return user_state_model_to_entity(row) if row else None

    async def save(self, state: UserState) -> None:
        existing = await self.get_current_by_user_id_and_direction(
            state.user_id, state.direction
        )
        if existing is not None:
            existing.supersede()
            old_model = await self._session.get(UserStateModel, existing.id.value)
            if old_model is not None:
                old_model.is_current = existing.is_current
        model = user_state_entity_to_model(state)
        self._session.add(model)

    async def delete(self, id: UserStateId, now: datetime | None = None) -> None:
        if now is None:
            now = datetime.now(tz=UTC)
        model = await self._session.get(UserStateModel, id.value)
        if model is not None:
            model.deleted_at = now

    async def exists(self, id: UserStateId) -> ExistsResult:
        query = select(UserStateModel).where(UserStateModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ExistsResult(row is not None)
