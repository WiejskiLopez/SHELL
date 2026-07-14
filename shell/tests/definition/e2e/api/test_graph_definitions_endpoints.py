"""E2E tests for Graph Definition endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.tests.shared.e2e_helpers import TEST_API_KEY, _make_app

if TYPE_CHECKING:
    import pathlib


class TestGraphDefinitionEndpoints:
    async def test_get_graph_definition_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/graph-definitions/base-planner-id",
                headers=headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "base-planner-id"
        assert "node_definitions" in data

    async def test_get_graph_definition_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/graph-definitions/nonexistent",
                headers=headers,
            )
        assert resp.status_code == 404

    async def test_graph_definition_by_semantic_request_validation(
        self,
        tmp_path: pathlib.Path,
    ) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/graph-definitions/by-semantic",
                json={},
                headers=headers,
            )
        assert resp.status_code == 422

    async def test_graph_definition_by_semantic_empty_body(
        self,
        tmp_path: pathlib.Path,
    ) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/graph-definitions/by-semantic",
                json={},
                headers=headers,
            )
        assert resp.status_code == 422
