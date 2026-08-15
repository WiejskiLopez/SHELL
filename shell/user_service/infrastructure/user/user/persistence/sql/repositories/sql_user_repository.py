from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.platform.domain.value_objects.exists_result import ExistsResult
from shell.user_service.domain.user.aggregates.user.repositories.user_repository import (
    UserRepository,
)
from shell.user_service.infrastructure.user.user.persistence.sql.mappers import (
    user_change_model,
    user_entity_to_model,
    user_model_to_entity,
)

from ..models import UserModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.user_service.domain.user.aggregates.user.user import User
    from shell.user_service.domain.user.value_objects.user_id import UserId


class SqlUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UserId) -> User | None:
        query = select(UserModel).where(UserModel.id == user_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return user_model_to_entity(row) if row else None

    async def save(self, user: User) -> None:
        model = await self._session.get(UserModel, user.id.value)
        if model is None:
            model = user_entity_to_model(user)
            self._session.add(model)
        else:
            user_change_model(model, user)

    async def delete(self, id: UserId, now: datetime | None = None) -> None:
        if now is None:
            now = datetime.now(tz=UTC)
        model = await self._session.get(UserModel, id.value)
        if model is not None and model.deleted_at is None:
            model.deleted_at = now

    async def exists(self, id: UserId) -> ExistsResult:
        query = select(UserModel).where(UserModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ExistsResult(row is not None)
