"""E2E tests for Node Execution endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.tests.shared.e2e_helpers import TEST_API_KEY, _make_app

if TYPE_CHECKING:
    import pathlib


class TestNodeExecutionEndpoints:
    async def test_get_node_execution_result_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/node-executions/nonexistent/result?workflow_id=w1",
                headers=headers,
            )
        assert resp.status_code == 404

    async def test_get_node_execution_result_missing_workflow_id(
        self, tmp_path: pathlib.Path,
    ) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/node-executions/nonexistent/result",
                headers=headers,
            )
        assert resp.status_code == 422
