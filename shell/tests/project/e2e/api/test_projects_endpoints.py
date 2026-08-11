"""E2E tests for Project endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.tests.project.e2e.conftest import TEST_API_KEY, make_project_app

if TYPE_CHECKING:
    import pathlib


class TestProjectEndpoints:
    async def test_list_projects_returns_page_structure(self, tmp_path: pathlib.Path) -> None:
        app = await make_project_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/projects", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert body["total"] >= 0
        assert body["page"] == 1
        assert "page_size" in body
        assert "has_more" in body

    async def test_list_projects_default_pagination(self, tmp_path: pathlib.Path) -> None:
        app = await make_project_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/projects", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 1
        assert body["page_size"] == 100
