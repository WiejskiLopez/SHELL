from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient
from shell.tests.conftest import _make_app

if TYPE_CHECKING:
    import pathlib


class TestNodesRouter:
    async def test_get_graph_node_execution_result_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/nodes/nonexistent-node/result?workflow_id=wf-x")
        assert resp.status_code == 404
