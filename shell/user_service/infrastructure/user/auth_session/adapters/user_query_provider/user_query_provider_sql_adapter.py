from __future__ import annotations

from typing import TYPE_CHECKING

from shell.user_service.domain.user.aggregates.auth_session.ports.user_query_provider import (
    UserQueryProvider,
)
from shell.user_service.domain.user.aggregates.auth_session.value_objects.user_reference import (
    UserReference,
)
from shell.user_service.domain.user.value_objects.user_id import UserId
from shell.user_service.domain.user.value_objects.user_status import UserStatus

if TYPE_CHECKING:
    from shell.user_service.domain.user.value_objects.user_email import UserEmail
    from shell.user_service.infrastructure.user.user.persistence.sql.services.user_query_service import (
        UserQueryService,
    )


class UserQueryProviderSqlAdapter(UserQueryProvider):
    def __init__(self, queries: UserQueryService) -> None:
        self._queries = queries

    async def get_by_email(self, email: UserEmail) -> UserReference | None:
        user_dto = await self._queries.get_by_email(email.value)
        if user_dto is None:
            return None
        return UserReference(
            id=UserId(user_dto.id),
            status=UserStatus(user_dto.status),
        )
