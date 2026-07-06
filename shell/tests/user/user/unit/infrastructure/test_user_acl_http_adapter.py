from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from shell.domain.user.value_objects.user_id import UserId
from shell.infrastructure.user.user.http.user_acl_http_adapter import UserAclHttpAdapter


class TestUserAclHttpAdapter:
    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        return AsyncMock(spec="httpx.AsyncClient")

    @pytest.fixture
    def adapter(self, mock_client: AsyncMock) -> UserAclHttpAdapter:
        return UserAclHttpAdapter(client=mock_client)

    async def test_get_user_raises_not_implemented_on_501(
        self,
        adapter: UserAclHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        mock_client.get = AsyncMock(return_value=Mock(status_code=501))
        with pytest.raises(NotImplementedError, match="User BC REST API not fully implemented yet"):
            await adapter.get_user(UserId("user-1"))

    async def test_get_user_calls_correct_endpoint(
        self,
        adapter: UserAclHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        mock_client.get = AsyncMock(
            return_value=Mock(status_code=200, json=Mock(return_value={"id": "user-1"}))
        )
        with pytest.raises(
            NotImplementedError, match="User deserialization from JSON not implemented yet"
        ):
            await adapter.get_user(UserId("user-1"))
        mock_client.get.assert_awaited_once_with("/api/v1/users/user-1")
