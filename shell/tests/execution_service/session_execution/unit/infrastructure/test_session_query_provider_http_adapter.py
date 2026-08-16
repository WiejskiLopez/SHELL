from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from shell.execution_service.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
    SessionIdRef,
)
from shell.execution_service.domain.execution.aggregates.session_execution.value_objects.session_reference import (
    SessionReference,
)
from shell.execution_service.infrastructure.execution.session_execution.adapters.session_query_provider.session_query_provider_http_adapter import (
    SessionQueryProviderHttpAdapter,
)


class TestSessionQueryProviderHttpAdapter:
    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        return AsyncMock(spec="httpx.AsyncClient")

    @pytest.fixture
    def adapter(self, mock_client: AsyncMock) -> SessionQueryProviderHttpAdapter:
        return SessionQueryProviderHttpAdapter(client=mock_client)

    async def test_get_by_id_returns_none_on_404(
        self,
        adapter: SessionQueryProviderHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        mock_client.get = AsyncMock(return_value=Mock(status_code=404))
        result = await adapter.get_by_id(SessionIdRef("nonexistent-session"))
        assert result is None

    async def test_get_by_id_maps_response(
        self,
        adapter: SessionQueryProviderHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        response_data = {
            "id": "session-1",
        }
        mock_client.get = AsyncMock(
            return_value=Mock(status_code=200, json=Mock(return_value=response_data))
        )
        result = await adapter.get_by_id(SessionIdRef("session-1"))
        assert isinstance(result, SessionReference)
        assert result.session_id == SessionIdRef("session-1")

    async def test_get_by_id_maps_only_required_field(
        self,
        adapter: SessionQueryProviderHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        response_data = {
            "id": "session-2",
        }
        mock_client.get = AsyncMock(
            return_value=Mock(status_code=200, json=Mock(return_value=response_data))
        )
        result = await adapter.get_by_id(SessionIdRef("session-2"))
        assert isinstance(result, SessionReference)
        assert result.session_id == SessionIdRef("session-2")

    async def test_raises_on_5xx(
        self,
        adapter: SessionQueryProviderHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        mock_client.get = AsyncMock(
            return_value=Mock(
                status_code=500, raise_for_status=Mock(side_effect=Exception("Server error"))
            )
        )
        with pytest.raises(Exception, match="Server error"):
            await adapter.get_by_id(SessionIdRef("session-1"))
