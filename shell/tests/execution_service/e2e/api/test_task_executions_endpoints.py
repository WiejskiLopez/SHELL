"""E2E tests for Task Execution endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.tests.execution_service.e2e.conftest import TEST_API_KEY, make_execution_app

if TYPE_CHECKING:
    import pathlib


class TestTaskExecutionEndpoints:
    async def test_list_task_executions_returns_page(self, tmp_path: pathlib.Path) -> None:
        app = await make_execution_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/task-executions", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert body["page"] == 1
        assert "page_size" in body
        assert "has_more" in body

    async def test_task_executions_default_pagination(self, tmp_path: pathlib.Path) -> None:
        app = await make_execution_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/task-executions", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 1
        assert body["page_size"] == 100
