from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from shell.domain.projekt.value_objects.project_id import ProjectId
from shell.infrastructure.projekt.http.project_acl_http_adapter import ProjectAclHttpAdapter


class TestProjectAclHttpAdapter:
    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        return AsyncMock(spec="httpx.AsyncClient")

    @pytest.fixture
    def adapter(self, mock_client: AsyncMock) -> ProjectAclHttpAdapter:
        return ProjectAclHttpAdapter(client=mock_client)

    async def test_get_project_raises_not_implemented_on_501(
        self,
        adapter: ProjectAclHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        mock_client.get = AsyncMock(return_value=Mock(status_code=501))
        with pytest.raises(
            NotImplementedError, match="Project BC REST API not fully implemented yet"
        ):
            await adapter.get_project(ProjectId("project-1"))

    async def test_get_project_calls_correct_endpoint(
        self,
        adapter: ProjectAclHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        mock_client.get = AsyncMock(
            return_value=Mock(status_code=200, json=Mock(return_value={"id": "project-1"}))
        )
        with pytest.raises(
            NotImplementedError, match="Project deserialization from JSON not implemented yet"
        ):
            await adapter.get_project(ProjectId("project-1"))
        mock_client.get.assert_awaited_once_with("/api/v1/projects/project-1")
