from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import exists as sa_exists
from sqlalchemy import select

from shell.domain.user.aggregates.auth_session.repositories.auth_session_repository import (
    AuthSessionRepository,
)
from shell.infrastructure.user.auth_session.persistence.sql.mappers import (
    auth_session_entity_to_model,
    auth_session_model_to_entity,
    auth_session_update_model,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult

from ..models import AuthSessionModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.user.aggregates.auth_session.auth_session import AuthSession
    from shell.domain.user.aggregates.auth_session.value_objects.auth_session_id import (
        AuthSessionId,
    )
    from shell.domain.user.value_objects.user_id import UserId
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.hash import Hash


class SqlAuthSessionRepository(AuthSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, auth_session: AuthSession) -> None:
        model = await self._session.get(AuthSessionModel, auth_session.id.value)
        if model is None:
            model = auth_session_entity_to_model(auth_session)
            self._session.add(model)
        else:
            auth_session_update_model(model, auth_session)

    async def get_by_id(self, auth_session_id: AuthSessionId) -> AuthSession | None:
        model = await self._session.get(AuthSessionModel, auth_session_id.value)
        if model is None:
            return None
        return auth_session_model_to_entity(model)

    async def get_by_token_hash(self, token_hash: Hash) -> AuthSession | None:
        query = select(AuthSessionModel).where(AuthSessionModel.token_hash == token_hash.value)
        model = (await self._session.execute(query)).scalar_one_or_none()
        if model is None:
            return None
        return auth_session_model_to_entity(model)

    async def get_active_by_user_id(self, user_id: UserId, now: CreatedAt) -> AuthSession | None:
        query = (
            select(AuthSessionModel)
            .where(
                AuthSessionModel.user_id == user_id.value,
                AuthSessionModel.revoked_at.is_(None),
                AuthSessionModel.deleted_at.is_(None),
                AuthSessionModel.expires_at > now.value,
            )
            .order_by(AuthSessionModel.created_at.desc())
            .limit(1)
        )
        model = (await self._session.execute(query)).scalar_one_or_none()
        if model is None:
            return None
        return auth_session_model_to_entity(model)

    async def delete(self, id: AuthSessionId) -> None:
        model = await self._session.get(AuthSessionModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: AuthSessionId) -> ExistsResult:
        stmt = select(sa_exists().where(AuthSessionModel.id == id.value))
        result = await self._session.execute(stmt)
        return ExistsResult(result.scalar() or False)


__all__ = [
    "SqlAuthSessionRepository",
]
