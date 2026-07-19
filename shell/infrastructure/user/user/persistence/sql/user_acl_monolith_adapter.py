"""Monolith UserACL — queries users directly from the SQL database."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.user.aggregates.user.user import User
from shell.domain.user.value_objects.user_email import UserEmail
from shell.domain.user.value_objects.user_id import UserId
from shell.domain.user.value_objects.user_status import UserStatus
from shell.infrastructure.user.user.persistence.sql.services.user_query_service import (
    UserQueryService,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class UserAclMonolithAdapter:
    """UserACL implementation for monolith mode — reads users from the same SQL database.

    In a microservice deployment this would be replaced by ``UserAclHttpAdapter``
    which calls the User BC over HTTP.
    """

    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._query_service = UserQueryService(session_factory)

    async def get_user(self, user_id: UserId) -> User:

        dto = await self._query_service.get_by_id(user_id.value)
        if dto is None:
            raise ValueError(f"User '{user_id.value}' not found")
        return User(
            id=UserId(dto.id),
            email=UserEmail(dto.email),
            status=UserStatus(dto.status),
            created_at=CreatedAt.from_datetime(dto.created_at),
            updated_at=UpdatedAt.from_datetime(dto.updated_at),
            deleted_at=DeletedAt.from_datetime(dto.deleted_at),
        )
