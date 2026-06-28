from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient
from shell.bootstrap.execution.factory.application_factory import ApplicationFactory
from shell.infrastructure.platform.configuration.shell_config import ShellConfig
from shell.tests.conftest_helpers import _make_app

if TYPE_CHECKING:
    import pathlib


class TestWorkflowsRouter:
    async def test_start_workflow_unknown_task_returns_error(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/workflows", json={"task_execution_id": "no_such_task"})
        assert resp.status_code in (400, 404)

    async def test_start_and_get_workflow(self, tmp_path: pathlib.Path) -> None:
        md = tmp_path / "wf_task_execution.md"
        md.write_text("# WF Task", encoding="utf-8")

        db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
        core_container = await ApplicationFactory(ShellConfig(database_url=db_url)).build()
        from shell.framework.platform.api.app import create_app

        app = create_app(core_container)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp_import = await client.post(
                "/task_executions/import",
                json={
                    "task_execution_name": "wf_task",
                    "md_path": str(md),
                },
            )
            assert resp_import.status_code == 201
            task_execution_id = resp_import.json()["task_execution_id"]

            resp = await client.post(
                "/workflows", json={"task_execution_id": task_execution_id}
            )

            assert resp.status_code == 201
