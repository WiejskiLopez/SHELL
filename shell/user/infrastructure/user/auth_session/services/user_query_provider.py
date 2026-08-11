from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from shell.user.domain.user.aggregates.auth_session.ports.user_query_provider import (
    UserQueryProvider,
)
from shell.user.domain.user.aggregates.user.user import User
from shell.user.domain.user.value_objects.user_email import UserEmail
from shell.user.domain.user.value_objects.user_id import UserId
from shell.user.domain.user.value_objects.user_status import UserStatus

if TYPE_CHECKING:
    from shell.user.infrastructure.user.user.persistence.sql.services.user_query_service import (
        UserQueryService,
    )


class SqlUserQueryProvider(UserQueryProvider):
    def __init__(self, queries: UserQueryService) -> None:
        self._queries = queries

    async def get_by_email(self, email: UserEmail) -> User | None:
        user_dto = await self._queries.get_by_email(email.value)
        if user_dto is None:
            return None
        return User.restore(
            id=UserId(user_dto.id),
            created_at=CreatedAt.from_datetime(user_dto.created_at),
            updated_at=UpdatedAt.from_datetime(user_dto.updated_at),
            deleted_at=DeletedAt.from_datetime(user_dto.deleted_at),
            email=UserEmail(user_dto.email),
            status=UserStatus(user_dto.status),
        )
