from __future__ import annotations

from datetime import UTC, datetime
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

    async def test_get_user_raises_on_http_error(
        self,
        adapter: UserAclHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        mock_response = Mock(status_code=404)
        mock_response.raise_for_status.side_effect = Exception("HTTP 404")
        mock_client.get = AsyncMock(return_value=mock_response)
        with pytest.raises(Exception, match="HTTP 404"):
            await adapter.get_user(UserId("user-1"))

    async def test_get_user_calls_correct_endpoint(
        self,
        adapter: UserAclHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        mock_response = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(
                return_value={
                    "id": "user-1",
                    "email": "user@test.com",
                    "status": "active",
                    "created_at": datetime(2025, 1, 1, tzinfo=UTC),
                    "updated_at": None,
                    "deleted_at": None,
                }
            ),
        )
        mock_client.get = AsyncMock(return_value=mock_response)
        user = await adapter.get_user(UserId("user-1"))
        assert user.id.value == "user-1"
        assert user._email.value == "user@test.com"
        mock_client.get.assert_awaited_once_with("/api/v1/users/user-1")
