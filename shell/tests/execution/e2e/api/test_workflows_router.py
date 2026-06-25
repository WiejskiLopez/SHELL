from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient
from shell.bootstrap.execution.factory.application_factory import ApplicationFactory
from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_node_execution import GraphNodeExecution
from shell.domain.execution.value_objects.ids import GraphExecutionId, GraphNodeExecutionId
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.platform.value_objects.mode import Mode
from shell.infrastructure.platform.configuration.shell_config import ShellConfig
from shell.tests.conftest import _make_app

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
            await client.post(
                "/task_executions/import",
                json={
                    "task_execution_name": "wf_task",
                    "md_path": str(md),
                },
            )

            unit_of_work_factory = core_container.infra.unit_of_work_factory()
            async with unit_of_work_factory as unit_of_work:
                task_execution = await unit_of_work.task_execution_repository.get_current_by_name(
                    TaskExecutionName("wf_task")
                )
                assert task_execution is not None

                actual_task_execution_id = task_execution.id.value

                existing_graph_execution = await unit_of_work.graph_execution_repository.get_by_task_execution_id(
                    task_execution.id
                )
                ge_id = (
                    existing_graph_execution.id
                    if existing_graph_execution
                    else GraphExecutionId.generate()
                )
                node = GraphNodeExecution(
                    id=GraphNodeExecutionId("wf_task-node-0"),
                    position=0,
                    mode=Mode("agent"),
                    role="agent",
                    node_type="agent",
                    graph_execution_id=ge_id,
                )
                await unit_of_work.graph_node_execution_repository.save(node)
                if existing_graph_execution:
                    existing_graph_execution.add_graph_node_execution_id(node.id)
                    await unit_of_work.graph_execution_repository.save(existing_graph_execution)
                    await unit_of_work.commit()
                else:
                    graph_execution = GraphExecution(
                        id=ge_id,
                        task_execution_id=task_execution.id,
                        graph_definition_id="tpl",
                        graph_node_execution_ids=[node.id],
                    )
                    await unit_of_work.graph_execution_repository.save(graph_execution)
                    await unit_of_work.commit()

            resp = await client.post(
                "/workflows", json={"task_execution_id": actual_task_execution_id}
            )

            assert resp.status_code == 201
