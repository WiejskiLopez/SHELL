"""E2E tests for Edge Link Execution endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.tests.shared.e2e_helpers import TEST_API_KEY, _make_app

if TYPE_CHECKING:
    import pathlib


class TestEdgeLinkExecutionEndpoints:
    async def test_create_edge_link_execution(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        payload = {
            "node_execution_id": "node-exec-1",
            "edge_execution_id": "edge-exec-1",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/edge-links", json=payload, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data

    async def test_create_edge_link_execution_empty_body(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/edge-links", json={}, headers=headers)
        assert resp.status_code == 422

    async def test_delete_edge_link_execution_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete("/api/v1/edge-links/nonexistent", headers=headers)
        assert resp.status_code == 404

    async def test_create_and_delete_edge_link_execution(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        payload = {
            "node_execution_id": "node-exec-2",
            "edge_execution_id": "edge-exec-2",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/edge-links",
                json=payload,
                headers=headers,
            )
        assert create_resp.status_code == 201
        link_id = create_resp.json()["id"]

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            delete_resp = await client.delete(
                f"/api/v1/edge-links/{link_id}",
                headers=headers,
            )
        assert delete_resp.status_code == 204
