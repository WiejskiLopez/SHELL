"""E2E API tests — FastAPI control plane."""
from __future__ import annotations

import pathlib

import pytest
from httpx import ASGITransport, AsyncClient


async def _make_app(tmp_path: pathlib.Path):  # type: ignore[return]
    from shell_ddd.bootstrap.container import ApplicationFactory
    from shell_ddd.framework.api.app import create_app

    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    container = await ApplicationFactory(database_url=db_url).build()
    return create_app(container)


class TestHealthEndpoint:
    async def test_health_returns_ok(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestTasksRouter:
    async def test_import_task(self, tmp_path: pathlib.Path) -> None:
        md = tmp_path / "api_task.md"
        yaml_ = tmp_path / "api_task.yaml"
        md.write_text("# API Task", encoding="utf-8")
        yaml_.write_text("graph:\n  nodes: []\n", encoding="utf-8")

        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/tasks/import", json={
                "task_name": "api_task",
                "md_path": str(md),
                "yaml_path": str(yaml_),
            })
        assert resp.status_code == 201
        assert "task_id" in resp.json()

    async def test_get_task_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/tasks/no_such_task")
        assert resp.status_code == 404


class TestWorkflowsRouter:
    async def test_start_workflow_unknown_task_returns_error(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/workflows", json={"task_name": "no_such_task"})
        # Domain error → 404 or 400
        assert resp.status_code in (400, 404)

    async def test_start_and_get_workflow(self, tmp_path: pathlib.Path) -> None:
        md = tmp_path / "wf_task.md"
        yaml_ = tmp_path / "wf_task.yaml"
        md.write_text("# WF Task", encoding="utf-8")
        yaml_.write_text("graph:\n  nodes: []\n", encoding="utf-8")

        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # import task first
            await client.post("/tasks/import", json={
                "task_name": "wf_task",
                "md_path": str(md),
                "yaml_path": str(yaml_),
            })
            # start workflow
            resp = await client.post("/workflows", json={"task_name": "wf_task"})
        assert resp.status_code == 201
        wf_id = resp.json()["workflow_id"]
        assert wf_id


class TestEnvelopesRouter:
    async def test_list_envelopes_empty(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/envelopes/workflow/nonexistent-wf")
        assert resp.status_code == 200
        assert resp.json()["envelopes"] == []


class TestNodesRouter:
    async def test_get_node_result_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/nodes/nonexistent-node/result?workflow_id=wf-x")
        assert resp.status_code == 404
