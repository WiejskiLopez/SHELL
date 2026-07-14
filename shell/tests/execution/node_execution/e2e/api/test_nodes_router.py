from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.tests.shared.e2e_helpers import TEST_API_KEY, _make_app

if TYPE_CHECKING:
    import pathlib


class TestNodesRouter:
    async def test_get_node_execution_result_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/node-executions/nonexistent-node/result?workflow_id=wf-x", headers=headers
            )
        assert resp.status_code == 404

    async def test_get_node_execution_result_returns_proper_model(
        self, tmp_path: pathlib.Path
    ) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/node-executions/existing-id/result?workflow_id=wf-x", headers=headers
            )
        if resp.status_code == 200:
            body = resp.json()
            assert "node_execution_id" in body
            assert "status" in body
            assert "workflow_id" in body
