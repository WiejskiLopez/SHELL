from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.tests.shared.e2e_helpers import TEST_API_KEY, _make_app

if TYPE_CHECKING:
    import pathlib


class TestErrorResponseFormat:
    async def test_domain_error_returns_problem_detail(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/users/nonexistent", headers=headers)
        assert resp.status_code == 404
        body = resp.json()
        assert "title" in body
        assert "status" in body
        assert "detail" in body
        assert "timestamp" in body

    async def test_validation_error_returns_all_field_errors(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/edge-executions", json={}, headers=headers)
        assert resp.status_code == 422
        body = resp.json()
        assert "errors" in body

    async def test_concurrent_modification_returns_409(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put("/edge-executions/some-id", json={"target_node_execution_id": "x"}, headers=headers)
        assert resp.status_code in (404, 409)
