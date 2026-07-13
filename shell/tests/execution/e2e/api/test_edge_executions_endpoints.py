"""E2E tests for Edge Execution endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.tests.shared.e2e_helpers import TEST_API_KEY, _make_app

if TYPE_CHECKING:
    import pathlib


class TestEdgeExecutionEndpoints:
    async def test_create_edge_execution(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        payload = {
            "edge_definition_id": "edge-def-1",
            "source_node_execution_id": "node-1",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/edge-executions", json=payload, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data

    async def test_create_edge_execution_empty_body(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/edge-executions", json={}, headers=headers)
        assert resp.status_code == 422

    async def test_update_edge_execution_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        payload = {"target_node_execution_id": "node-2"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(
                "/api/v1/edge-executions/nonexistent", json=payload, headers=headers,
            )
        assert resp.status_code == 404

    async def test_delete_edge_execution_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete("/api/v1/edge-executions/nonexistent", headers=headers)
        assert resp.status_code == 404

    async def test_create_update_delete_edge_execution_flow(
        self, tmp_path: pathlib.Path,
    ) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        payload = {
            "edge_definition_id": "edge-def-2",
            "source_node_execution_id": "node-10",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/edge-executions", json=payload, headers=headers,
            )
        assert create_resp.status_code == 201
        edge_id = create_resp.json()["id"]

        update_payload = {"target_node_execution_id": "node-20"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            update_resp = await client.put(
                f"/api/v1/edge-executions/{edge_id}", json=update_payload, headers=headers,
            )
        assert update_resp.status_code == 200

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            delete_resp = await client.delete(
                f"/api/v1/edge-executions/{edge_id}", headers=headers,
            )
        assert delete_resp.status_code == 204
