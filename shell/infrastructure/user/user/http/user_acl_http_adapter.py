from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.user.aggregates.user.user import User
from shell.domain.user.ports.user_acl import UserACL
from shell.domain.user.value_objects.user_email import UserEmail
from shell.domain.user.value_objects.user_id import UserId
from shell.domain.user.value_objects.user_status import UserStatus
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    import httpx


class UserAclHttpAdapter(UserACL):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_user(self, user_id: UserId) -> User:
        response = await self._client.get(f"/api/v1/users/{user_id.value}")
        response.raise_for_status()
        data = response.json()
        return User(
            id=UserId(data["id"]),
            email=UserEmail(data["email"]),
            status=UserStatus(data["status"]),
            created_at=CreatedAt.from_datetime(data["created_at"])
            if data.get("created_at")
            else None,
            updated_at=UpdatedAt.from_datetime(data["updated_at"])
            if data.get("updated_at")
            else None,
            deleted_at=DeletedAt.from_datetime(data["deleted_at"])
            if data.get("deleted_at")
            else None,
        )
