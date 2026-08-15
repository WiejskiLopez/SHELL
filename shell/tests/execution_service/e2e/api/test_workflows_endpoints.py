"""E2E tests for Workflow endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.tests.execution_service.e2e.conftest import TEST_API_KEY, make_execution_app

if TYPE_CHECKING:
    import pathlib


class TestWorkflowEndpoints:
    async def test_list_workflows_returns_page(self, tmp_path: pathlib.Path) -> None:
        app = await make_execution_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/workflows", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert body["page"] == 1
        assert "page_size" in body
        assert "has_more" in body

    async def test_workflows_default_pagination(self, tmp_path: pathlib.Path) -> None:
        app = await make_execution_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/workflows", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 1
        assert body["page_size"] == 100

    async def test_get_workflow_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await make_execution_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/workflows/nonexistent", headers=headers)
        assert resp.status_code == 404

    async def test_get_workflow_by_id(self, tmp_path: pathlib.Path) -> None:
        app = await make_execution_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/workflows/some-workflow-id", headers=headers)
        assert resp.status_code == 404
