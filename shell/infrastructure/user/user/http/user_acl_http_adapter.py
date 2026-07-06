from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.user.ports.user_acl import UserACL

if TYPE_CHECKING:
    import httpx

    from shell.domain.user.aggregates.user.user import User
    from shell.domain.user.value_objects.user_id import UserId


class UserAclHttpAdapter(UserACL):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_user(self, user_id: UserId) -> User:
        response = await self._client.get(f"/api/v1/users/{user_id}")
        if response.status_code == 501:
            raise NotImplementedError("User BC REST API not fully implemented yet")
        response.raise_for_status()
        data = response.json()
        raise NotImplementedError(
            f"User deserialization from JSON not implemented yet. Got: {data}"
        )
