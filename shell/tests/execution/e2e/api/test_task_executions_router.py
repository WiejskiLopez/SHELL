from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.tests.e2e.api.conftest import _make_app

if TYPE_CHECKING:
    import pathlib


class TestTaskExecutionsRouter:
    async def test_import_task_execution(self, tmp_path: pathlib.Path) -> None:
        md = tmp_path / "api_task_execution.md"
        md.write_text("# API Task", encoding="utf-8")

        app = await _make_app(tmp_path)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/task_executions/import",
                json={
                    "task_execution_name": "api_task",
                    "md_path": str(md),
                },
            )
        assert resp.status_code == 201
        assert "task_execution_id" in resp.json()

    async def test_get_task_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/task_executions/no_such_task")
        assert resp.status_code == 404
