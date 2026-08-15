from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.user_service.application.user.auth_session.dto.current_auth_session import (
    CurrentAuthSessionDto,
)
from shell.user_service.infrastructure.user.auth_session.persistence.sql.models.auth_session import (
    AuthSessionModel,
)

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class AuthSessionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_active_by_token_hash(
        self,
        token_hash: str,
        now: datetime,
    ) -> CurrentAuthSessionDto | None:
        async with self._session_factory() as session:
            stmt = select(AuthSessionModel).where(
                AuthSessionModel.token_hash == token_hash,
                AuthSessionModel.revoked_at.is_(None),
                AuthSessionModel.deleted_at.is_(None),
                AuthSessionModel.expires_at > now,
            )
            model = (await session.execute(stmt)).scalar_one_or_none()
            if model is None:
                return None
            return CurrentAuthSessionDto(
                auth_session_id=model.id,
                user_id=model.user_id,
            )
