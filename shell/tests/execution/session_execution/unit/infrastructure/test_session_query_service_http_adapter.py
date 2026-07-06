from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from shell.application.session.session.dto.session import SessionDto
from shell.infrastructure.execution.session_execution.http.session_query_service_http_adapter import (
    SessionQueryServiceHttpAdapter,
)


class TestSessionQueryServiceHttpAdapter:
    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        return AsyncMock(spec="httpx.AsyncClient")

    @pytest.fixture
    def adapter(self, mock_client: AsyncMock) -> SessionQueryServiceHttpAdapter:
        return SessionQueryServiceHttpAdapter(client=mock_client)

    async def test_get_session_history_returns_none_on_404(
        self,
        adapter: SessionQueryServiceHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        mock_client.get = AsyncMock(return_value=Mock(status_code=404))
        result = await adapter.get_session_history("nonexistent-session")
        assert result is None

    async def test_get_session_history_maps_response(
        self,
        adapter: SessionQueryServiceHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        response_data = {
            "id": "session-1",
            "goal": "test goal",
            "status": "opened",
            "opened_at": "2024-01-01T00:00:00",
            "closed_at": None,
        }
        mock_client.get = AsyncMock(
            return_value=Mock(status_code=200, json=Mock(return_value=response_data))
        )
        result = await adapter.get_session_history("session-1")
        assert isinstance(result, SessionDto)
        assert result.id == "session-1"
        assert result.goal == "test goal"
        assert result.status == "opened"
        assert result.closed_at is None

    async def test_get_session_history_with_closed_at(
        self,
        adapter: SessionQueryServiceHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        response_data = {
            "id": "session-2",
            "goal": "another goal",
            "status": "closed",
            "opened_at": "2024-01-01T00:00:00",
            "closed_at": "2024-01-02T00:00:00",
        }
        mock_client.get = AsyncMock(
            return_value=Mock(status_code=200, json=Mock(return_value=response_data))
        )
        result = await adapter.get_session_history("session-2")
        assert isinstance(result, SessionDto)
        assert result.closed_at is not None

    async def test_raises_on_5xx(
        self,
        adapter: SessionQueryServiceHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        mock_client.get = AsyncMock(
            return_value=Mock(
                status_code=500, raise_for_status=Mock(side_effect=Exception("Server error"))
            )
        )
        with pytest.raises(Exception, match="Server error"):
            await adapter.get_session_history("session-1")
